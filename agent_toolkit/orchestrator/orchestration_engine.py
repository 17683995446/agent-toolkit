"""Orchestration engine for tool chain execution."""

import asyncio
import uuid
from typing import Any, Optional, Dict, List
from datetime import datetime

from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainNode,
    ExecutionContext,
    NodeExecutionResult,
    NodeType,
    ExecutionMode,
    ChainStatus,
    RetryPolicy,
)
from agent_toolkit.orchestrator.node_executors import (
    ToolNodeExecutor,
    ConditionNodeExecutor,
    LoopNodeExecutor,
    ParallelNodeExecutor,
    MergeNodeExecutor,
    InputNodeExecutor,
    OutputNodeExecutor
)
from agent_toolkit.shared.structured_logging import LoggerMixin


class OrchestrationEngine(LoggerMixin):
    """Engine for executing tool chains."""

    def __init__(self, tool_registry: Any = None):
        self._active_executions: Dict[str, ExecutionContext] = {}
        self._node_executors: Dict[NodeType, Any] = {}
        self._executors: Dict[NodeType, Any] = {}
        
        # 注册默认执行器
        self._register_default_executors(tool_registry)

    def _register_default_executors(self, tool_registry: Any = None):
        """注册默认节点执行器。"""
        self.register_node_executor(NodeType.TOOL, ToolNodeExecutor(tool_registry))
        self.register_node_executor(NodeType.CONDITION, ConditionNodeExecutor())
        self.register_node_executor(NodeType.LOOP, LoopNodeExecutor())
        self.register_node_executor(NodeType.PARALLEL, ParallelNodeExecutor())
        self.register_node_executor(NodeType.MERGE, MergeNodeExecutor())
        self.register_node_executor(NodeType.INPUT, InputNodeExecutor())
        self.register_node_executor(NodeType.OUTPUT, OutputNodeExecutor())

    def register_node_executor(self, node_type: NodeType, executor: Any) -> None:
        """Register an executor for a node type."""
        self._node_executors[node_type] = executor
        self._executors[node_type] = executor  # 同步到 _executors 属性
        self.logger.info("node_executor_registered", node_type=node_type.value)

    async def execute_chain(
        self,
        chain: ToolChain,
        initial_inputs: Dict[str, Any],
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """Execute a tool chain."""
        execution_id = str(uuid.uuid4())
        
        is_valid, errors = chain.validate()
        if not is_valid:
            raise ValueError(f"Invalid chain: {errors}")

        context = ExecutionContext(
            execution_id=execution_id,
            chain_id=chain.id,
            variables=initial_inputs,
            metadata=context_metadata or {}
        )

        self._active_executions[execution_id] = context

        self.logger.info(
            "chain_execution_started",
            execution_id=execution_id,
            chain_id=chain.id,
            mode=chain.execution_mode.value
        )

        try:
            if chain.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(chain, context)
            elif chain.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(chain, context)
            elif chain.execution_mode == ExecutionMode.DAG:
                await self._execute_dag(chain, context)
            else:
                raise ValueError(f"Unknown execution mode: {chain.execution_mode}")

            context.status = ChainStatus.COMPLETED

        except Exception as e:
            context.status = ChainStatus.FAILED
            context.errors.append({
                "type": "execution_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            self.logger.error("chain_execution_failed", execution_id=execution_id, error=str(e))

        finally:
            context.end_time = datetime.utcnow()
            self.logger.info(
                "chain_execution_completed",
                execution_id=execution_id,
                status=context.status.value,
                duration_ms=(context.end_time - context.start_time).total_seconds() * 1000
            )

        return context

    async def _execute_sequential(self, chain: ToolChain, context: ExecutionContext) -> None:
        """Execute chain sequentially."""
        sorted_nodes = chain.topological_sort()

        for node in sorted_nodes:
            if context.status == ChainStatus.FAILED:
                break

            if not self._should_execute_node(chain, node, context):
                self.logger.debug("node_skipped", node_id=node.id)
                continue

            result = await self._execute_node(node, context)
            context.node_results[node.id] = result

            if not result.output:
                self.logger.warning("node_returned_no_output", node_id=node.id)

    async def _execute_parallel(self, chain: ToolChain, context: ExecutionContext) -> None:
        """Execute chain with parallel node execution."""
        nodes_by_level = self._group_nodes_by_level(chain)

        for level_nodes in nodes_by_level:
            if context.status == ChainStatus.FAILED:
                break

            tasks = []
            for node in level_nodes:
                if self._should_execute_node(chain, node, context):
                    task = self._execute_node(node, context)
                    tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for node, result in zip(level_nodes, results):
                    if isinstance(result, Exception):
                        context.node_results[node.id] = NodeExecutionResult(
                            node_id=node.id,
                            status="failed",
                            error=str(result),
                            start_time=datetime.utcnow()
                        )
                        context.status = ChainStatus.FAILED
                    else:
                        context.node_results[node.id] = result

    async def _execute_dag(self, chain: ToolChain, context: ExecutionContext) -> None:
        """Execute chain following DAG structure."""
        await self._execute_sequential(chain, context)

    def _group_nodes_by_level(self, chain: ToolChain) -> List[List[ChainNode]]:
        """Group nodes by execution level for parallel execution."""
        levels = []
        remaining = list(chain.nodes)
        processed = set()

        while remaining:
            current_level = []
            next_remaining = []

            for node in remaining:
                predecessors = chain.get_predecessors(node.id)
                if all(p.id in processed for p in predecessors):
                    current_level.append(node)
                else:
                    next_remaining.append(node)

            if not current_level:
                current_level = next_remaining[:1]
                next_remaining = next_remaining[1:]

            levels.append(current_level)
            for node in current_level:
                processed.add(node.id)
            remaining = next_remaining

        return levels

    def _should_execute_node(self, chain: ToolChain, node: ChainNode, context: ExecutionContext) -> bool:
        """Check if a node should be executed based on conditions."""
        if node.condition:
            try:
                result = self._evaluate_condition(node.condition, context)
                if not result:
                    return False
            except Exception as e:
                self.logger.warning(
                    "condition_evaluation_failed",
                    node_id=node.id,
                    condition=node.condition,
                    error=str(e)
                )
                return False

        return True

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a condition expression."""
        variables = context.variables.copy()
        variables.update(context.node_results)

        try:
            result = eval(condition, {"__builtins__": {}}, variables)
            return bool(result)
        except Exception as e:
            self.logger.error("condition_eval_error", condition=condition, error=str(e))
            return False

    async def _execute_node(self, node: ChainNode, context: ExecutionContext) -> NodeExecutionResult:
        """Execute a single node."""
        start_time = datetime.utcnow()
        retry_count = 0
        max_attempts = node.retry_policy.max_attempts if node.retry_policy else 1

        self.logger.info("node_execution_started", node_id=node.id, node_type=node.type.value)

        while retry_count < max_attempts:
            try:
                input_data = self._prepare_node_input(node, context)

                executor = self._node_executors.get(node.type)
                if not executor:
                    raise ValueError(f"No executor registered for node type: {node.type}")

                output = await executor.execute(node, input_data, context)

                end_time = datetime.utcnow()

                self.logger.info(
                    "node_execution_completed",
                    node_id=node.id,
                    retry_count=retry_count,
                    duration_ms=(end_time - start_time).total_seconds() * 1000
                )

                context.variables.update(output)

                return NodeExecutionResult(
                    node_id=node.id,
                    status="success",
                    output=output,
                    start_time=start_time,
                    end_time=end_time,
                    retry_count=retry_count
                )

            except Exception as e:
                retry_count += 1
                self.logger.warning(
                    "node_execution_retry",
                    node_id=node.id,
                    attempt=retry_count,
                    max_attempts=max_attempts,
                    error=str(e)
                )

                if retry_count < max_attempts:
                    delay = (node.retry_policy.retry_delay * 
                            (node.retry_policy.backoff_multiplier ** (retry_count - 1))
                            if node.retry_policy else 1)
                    await asyncio.sleep(delay)

        end_time = datetime.utcnow()

        return NodeExecutionResult(
            node_id=node.id,
            status="failed",
            error=f"Max retries ({max_attempts}) exceeded",
            start_time=start_time,
            end_time=end_time,
            retry_count=retry_count
        )

    def _prepare_node_input(self, node: ChainNode, context: ExecutionContext) -> Dict[str, Any]:
        """Prepare input data for node execution."""
        input_data = {}
        for key, value_path in node.inputs.items():
            if value_path in context.variables:
                input_data[key] = context.variables[value_path]
            elif value_path in context.node_results:
                input_data[key] = context.node_results[value_path]
            else:
                input_data[key] = value_path
        return input_data

    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get an active execution context."""
        return self._active_executions.get(execution_id)

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        if execution_id in self._active_executions:
            self._active_executions[execution_id].status = ChainStatus.CANCELLED
            self.logger.info("execution_cancelled", execution_id=execution_id)
            return True
        return False

    def list_active_executions(self) -> List[str]:
        """List all active execution IDs."""
        return list(self._active_executions.keys())
