"""
Chain execution engine.

Executes tool chains by resolving dependencies, evaluating conditions,
and managing the execution flow.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from agent_toolkit.models.chain_orchestration_models import ChainDefinition, ChainExecution, ChainNode
from agent_toolkit.models.runtime_execution_models import ExecutionStatus
from agent_toolkit.models.tool_definition_models import ToolExecutionRequest, ToolExecutionResult
from agent_toolkit.observability.opentelemetry_tracing_setup import trace_chain_execution
from agent_toolkit.observability.prometheus_metrics_definition import (
    chain_execution_total,
    chain_execution_duration_seconds,
)
from agent_toolkit.runtime.tool_runtime_service import ToolRuntimeService

logger = logging.getLogger(__name__)


class ChainExecutionEngine:
    """
    Execution engine for tool chains.

    Resolves node dependencies, evaluates conditions, and executes
    nodes in the correct order using topological sorting.
    """

    def __init__(self, runtime_service: ToolRuntimeService) -> None:
        """
        Initialize the chain execution engine.

        Args:
            runtime_service: Runtime service for executing individual tools.
        """
        self._runtime = runtime_service

    async def execute_chain(
        self,
        chain: ChainDefinition,
        initial_parameters: dict[str, Any] | None = None,
    ) -> ChainExecution:
        """
        Execute a complete tool chain.

        Args:
            chain: Chain definition with nodes and dependencies.
            initial_parameters: Initial parameters available to all nodes.

        Returns:
            ChainExecution with per-node results and overall status.
        """
        chain_id = f"chain-{uuid4().hex[:12]}"
        initial_parameters = initial_parameters or {}
        start_time = time.monotonic()

        execution = ChainExecution(
            chain_id=chain_id,
            chain_name=chain.name,
            status=ExecutionStatus.RUNNING,
            results={},
            started_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Starting chain execution '%s' for chain '%s' with %d nodes",
            chain_id,
            chain.name,
            len(chain.nodes),
        )

        try:
            with trace_chain_execution(chain.name, {"chain_id": chain_id}):
                # Build dependency graph and resolve execution order
                execution_order = self._resolve_execution_order(chain.nodes)

                # Execute nodes in order
                node_results: dict[str, Any] = {"input": initial_parameters}

                for node in execution_order:
                    node_id = node.node_id

                    # Check if this node should execute (condition evaluation)
                    if node.condition and not self._evaluate_condition(node.condition, node_results):
                        logger.info("Skipping node '%s' (condition not met)", node_id)
                        execution.results[node_id] = {
                            "status": "skipped",
                            "reason": "Condition not met",
                        }
                        continue

                    # Check dependencies succeeded
                    deps_ok = all(
                        execution.results.get(dep, {}).get("status") == "completed"
                        for dep in node.dependencies
                    )
                    if not deps_ok:
                        failed_deps = [
                            dep for dep in node.dependencies
                            if execution.results.get(dep, {}).get("status") != "completed"
                        ]
                        execution.results[node_id] = {
                            "status": "failed",
                            "reason": f"Dependencies failed: {failed_deps}",
                        }
                        execution.status = ExecutionStatus.FAILED
                        execution.error = f"Chain failed at node '{node_id}': dependencies {failed_deps} did not complete"
                        break

                    # Resolve parameters (replace {{node_id.field}} references)
                    resolved_params = self._resolve_parameters(node.parameters, node_results)

                    # Execute the tool with timeout and retry support
                    request = ToolExecutionRequest(
                        tool_name=node.tool_name,
                        parameters=resolved_params,
                    )

                    async def _execute_with_retry() -> Any:
                        """Execute tool with retry logic."""
                        last_error = None
                        max_retries = node.retry_count or 0

                        for attempt in range(max_retries + 1):
                            try:
                                # Apply timeout if specified
                                timeout = node.timeout
                                if timeout is not None and timeout > 0:
                                    result = await asyncio.wait_for(
                                        self._runtime.execute_tool(request),
                                        timeout=timeout
                                    )
                                else:
                                    result = await self._runtime.execute_tool(request)
                                return result
                            except asyncio.TimeoutError as te:
                                last_error = f"Timeout after {timeout}s"
                                logger.warning(
                                    "Node '%s' timeout on attempt %d/%d",
                                    node_id, attempt + 1, max_retries + 1
                                )
                                if attempt < max_retries:
                                    await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
                            except Exception as e:
                                last_error = str(e)
                                if attempt < max_retries:
                                    logger.warning(
                                        "Node '%s' failed on attempt %d/%d: %s",
                                        node_id, attempt + 1, max_retries + 1, e
                                    )
                                    await asyncio.sleep(0.1 * (attempt + 1))
                                else:
                                    raise

                        # All retries exhausted
                        raise RuntimeError(f"All {max_retries + 1} attempts failed. Last error: {last_error}")

                    try:
                        result = await _execute_with_retry()
                        execution.results[node_id] = {
                            "status": "completed" if result.success else "failed",
                            "success": result.success,
                            "output": result.output,
                            "error": result.error,
                            "execution_time": result.execution_time,
                        }

                        if not result.success:
                            # 处理 on_failure 策略
                            on_failure = node.on_failure or "stop"
                            if on_failure == "stop":
                                execution.status = ExecutionStatus.FAILED
                                execution.error = f"Chain failed at node '{node_id}': {result.error}"
                                break
                            elif on_failure == "continue":
                                # 继续执行，但标记为失败
                                logger.warning("Node '%s' failed but on_failure='continue', continuing chain", node_id)
                                node_results[node_id] = result.output or {}
                                continue
                            elif on_failure == "skip":
                                # 跳过此节点，不存储输出
                                logger.warning("Node '%s' failed but on_failure='skip', skipping node", node_id)
                                continue
                            else:
                                # 未知策略，默认停止
                                execution.status = ExecutionStatus.FAILED
                                execution.error = f"Chain failed at node '{node_id}': {result.error}"
                                break

                        # Store output for dependent nodes
                        node_results[node_id] = result.output or {}

                    except (RuntimeError, ValueError, TypeError) as exc:
                        execution.results[node_id] = {
                            "status": "failed",
                            "error": str(exc),
                        }
                        # 处理异常时的 on_failure 策略
                        on_failure = node.on_failure or "stop"
                        if on_failure == "stop":
                            execution.status = ExecutionStatus.FAILED
                            execution.error = f"Chain failed at node '{node_id}': {exc}"
                            break
                        elif on_failure in ("continue", "skip"):
                            logger.warning("Node '%s' raised exception but on_failure='%s', continuing chain: %s", node_id, on_failure, exc)
                            if on_failure == "continue":
                                node_results[node_id] = {}
                            continue
                        else:
                            execution.status = ExecutionStatus.FAILED
                            execution.error = f"Chain failed at node '{node_id}': {exc}"
                            break

                if execution.status == ExecutionStatus.RUNNING:
                    execution.status = ExecutionStatus.COMPLETED

        except ValueError:
            # 将拓扑排序中的 ValueError（如循环依赖检测）直接向上传播，
            # 而不是静默捕获为 FAILED 状态
            raise
        except Exception as exc:
            execution.status = ExecutionStatus.FAILED
            execution.error = f"Chain execution error: {exc}"
            logger.error("Chain execution '%s' failed: %s", chain_id, exc, exc_info=True)

        execution.completed_at = datetime.now(timezone.utc)

        # 记录 Prometheus 指标
        duration = time.monotonic() - start_time
        status = "success" if execution.status == ExecutionStatus.COMPLETED else "error"
        chain_execution_total.labels(chain_name=chain.name, status=status).inc()
        chain_execution_duration_seconds.labels(chain_name=chain.name).observe(duration)

        logger.info(
            "Chain execution '%s' completed with status: %s",
            chain_id,
            execution.status.value,
        )
        return execution

    def _resolve_execution_order(self, nodes: list[ChainNode]) -> list[ChainNode]:
        """
        Resolve the execution order of chain nodes using topological sort.

        Args:
            nodes: List of chain nodes.

        Returns:
            Nodes ordered for execution (dependencies first).

        Raises:
            ValueError: If circular dependencies are detected.
        """
        node_map: dict[str, ChainNode] = {n.node_id: n for n in nodes}
        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[ChainNode] = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError(f"Circular dependency detected involving node '{node_id}'")

            visiting.add(node_id)
            node = node_map.get(node_id)
            if node:
                for dep_id in node.dependencies:
                    # 检测引用了不存在的依赖节点
                    if dep_id not in node_map:
                        raise ValueError(
                            f"Node '{node_id}' depends on non-existent node '{dep_id}'"
                        )
                    visit(dep_id)
                order.append(node)

            visiting.discard(node_id)
            visited.add(node_id)

        for node in nodes:
            visit(node.node_id)

        return order

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """
        Evaluate a conditional expression against the execution context.

        Supports simple expressions like:
            - "result.search.output.total > 0"
            - "input.query != ''"
            - "{{n1.status}} == 'completed'"

        Args:
            condition: Conditional expression string.
            context: Execution context with node results.

        Returns:
            True if the condition evaluates to true.
        """
        try:
            # Replace dot-notation references with context lookups
            # Simple safe evaluation: only allow comparison operators
            safe_condition = condition.strip()

            # 首先解析 {{reference}} 模板语法
            def resolve_template(match: re.Match[str]) -> str:
                ref_path = match.group(1)
                ref_value = self._resolve_reference(ref_path, context)
                # 返回字符串表示，用于后续比较
                if ref_value is None:
                    return "None"
                elif isinstance(ref_value, str):
                    return f"'{ref_value}'"
                else:
                    return str(ref_value)

            safe_condition = re.sub(r"\{\{([\w.]+)\}\}", resolve_template, safe_condition)

            # Check for empty string comparison
            if "== ''" in safe_condition or '!= ""' in safe_condition:
                parts = re.split(r"(== ''|!= '')", safe_condition)
                if len(parts) == 3:
                    ref_path = parts[0].strip()
                    operator = parts[1].strip()
                    value = self._resolve_reference(ref_path, context)
                    if operator == "== ''":
                        return str(value).strip() == ""
                    elif operator == "!= ''":
                        return str(value).strip() != ""

            # Check for numeric comparison
            match = re.match(r"([\w.]+)\s*(>|>=|<=|==|!=)\s*(.+)", safe_condition)
            if match:
                ref_path, operator, value_str = match.groups()
                ref_value = self._resolve_reference(ref_path, context)
                compare_value = self._parse_value(value_str)

                if operator == ">":
                    return ref_value > compare_value
                elif operator == "<":
                    return ref_value < compare_value
                elif operator == ">=":
                    return ref_value >= compare_value
                elif operator == "<=":
                    return ref_value <= compare_value
                elif operator == "==":
                    return ref_value == compare_value
                elif operator == "!=":
                    return ref_value != compare_value

            # Default: evaluate as boolean reference
            value = self._resolve_reference(safe_condition, context)
            return bool(value)

        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Condition evaluation failed for '%s': %s", condition, exc)
            return False

    def _resolve_reference(self, path: str, context: dict[str, Any]) -> Any:
        """
        Resolve a dot-notation reference path against the context.

        Args:
            path: Dot-notation path (e.g., "search.output.total").
            context: Execution context.

        Returns:
            Resolved value or None if not found.
        """
        parts = path.strip().split(".")
        current: Any = context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None

        return current

    def _resolve_parameters(
        self,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Resolve parameter template references.

        Replaces {{node_id.field}} patterns with actual values from context.

        Args:
            parameters: Template parameters with {{references}}.
            context: Execution context.

        Returns:
            Resolved parameters with references replaced.
        """
        resolved: dict[str, Any] = {}

        for key, value in parameters.items():
            if isinstance(value, str):
                # Replace {{reference}} patterns
                def replacer(match: re.Match[str]) -> str:
                    ref_path = match.group(1)
                    ref_value = self._resolve_reference(ref_path, context)
                    return str(ref_value) if ref_value is not None else match.group(0)

                resolved[key] = re.sub(r"\{\{([\w.]+)\}\}", replacer, value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_parameters(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_parameters({"_v": v}, context)["_v"]
                    if isinstance(v, (str, dict))
                    else v
                    for v in value
                ]
            else:
                resolved[key] = value

        return resolved

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """
        Parse a string value into the appropriate Python type.

        Args:
            value_str: String representation of a value.

        Returns:
            Parsed value (int, float, str, bool).
        """
        value_str = value_str.strip().strip("'\"")
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False
        try:
            return int(value_str)
        except ValueError:
            pass
        try:
            return float(value_str)
        except ValueError:
            pass
        return value_str
