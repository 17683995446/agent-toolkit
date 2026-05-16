"""Node executors for different node types."""

from typing import Any, Dict, Optional
from datetime import datetime
import asyncio

from agent_toolkit.shared.structured_logging import LoggerMixin
from agent_toolkit.orchestrator.orchestration_models import (
    ChainNode,
    ExecutionContext,
    NodeType,
)


class BaseNodeExecutor(LoggerMixin):
    """Base class for node executors."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute the node."""
        raise NotImplementedError


class ToolNodeExecutor(BaseNodeExecutor):
    """Executor for TOOL type nodes."""

    def __init__(self, tool_registry: Any):
        self._tool_registry = tool_registry

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a tool node."""
        tool_id = node.config.get("tool_id")
        tool_version = node.config.get("version")

        self.logger.info(
            "executing_tool_node",
            node_id=node.id,
            tool_id=tool_id,
            version=tool_version
        )

        # TODO: Implement actual tool execution via adapter
        # For now, return mock result
        mock_result = {
            "tool_id": tool_id,
            "version": tool_version,
            "input": input_data,
            "output": {"result": "success", "timestamp": datetime.utcnow().isoformat()},
            "executed_at": datetime.utcnow().isoformat()
        }

        return mock_result


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executor for CONDITION type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a condition node."""
        condition = node.config.get("condition", "True")
        variables = context.variables.copy()
        variables.update(input_data)

        try:
            result = eval(condition, {"__builtins__": {}}, variables)
            return {"condition_met": bool(result), "result": result}
        except Exception as e:
            self.logger.error(
                "condition_evaluation_failed",
                node_id=node.id,
                condition=condition,
                error=str(e)
            )
            return {"condition_met": False, "error": str(e)}


class LoopNodeExecutor(BaseNodeExecutor):
    """Executor for LOOP type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a loop node."""
        iterable = node.config.get("iterable", [])
        var_name = node.config.get("variable", "item")
        max_iterations = node.config.get("max_iterations", 100)

        results = []
        count = 0

        self.logger.info(
            "executing_loop_node",
            node_id=node.id,
            iterable_length=len(iterable) if isinstance(iterable, list) else "unknown",
            max_iterations=max_iterations
        )

        # Get the iterable from variables or config
        if isinstance(iterable, str) and iterable in context.variables:
            actual_iterable = context.variables[iterable]
        else:
            actual_iterable = iterable

        if not isinstance(actual_iterable, list):
            actual_iterable = [actual_iterable]

        # Simulate loop execution
        # In a real implementation, this would execute child nodes
        for item in actual_iterable[:max_iterations]:
            loop_context = context.variables.copy()
            loop_context[var_name] = item

            results.append({
                "iteration": count,
                var_name: item,
                "timestamp": datetime.utcnow().isoformat()
            })
            count += 1

        return {
            "iterations": results,
            "total": count,
            "completed": True
        }


class ParallelNodeExecutor(BaseNodeExecutor):
    """Executor for PARALLEL type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a parallel node."""
        branch_ids = node.config.get("branches", [])
        timeout = node.config.get("timeout", 300)

        self.logger.info(
            "executing_parallel_node",
            node_id=node.id,
            branch_count=len(branch_ids),
            timeout=timeout
        )

        # Mock parallel execution
        # In a real implementation, this would execute all branches in parallel
        results = {}
        for branch_id in branch_ids:
            results[branch_id] = {
                "branch_id": branch_id,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "branches": results,
            "all_completed": True
        }


class MergeNodeExecutor(BaseNodeExecutor):
    """Executor for MERGE type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a merge node."""
        merge_strategy = node.config.get("strategy", "all")

        self.logger.info(
            "executing_merge_node",
            node_id=node.id,
            merge_strategy=merge_strategy
        )

        # Collect results from all predecessors
        merged = {}
        for node_id, result in context.node_results.items():
            if hasattr(result, 'output'):
                merged[node_id] = result.output
            else:
                merged[node_id] = result

        return {
            "merged": merged,
            "strategy": merge_strategy,
            "total_sources": len(merged)
        }


class InputNodeExecutor(BaseNodeExecutor):
    """Executor for INPUT type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute an input node."""
        schema = node.config.get("schema", {})
        default_value = node.config.get("default")

        self.logger.info(
            "executing_input_node",
            node_id=node.id,
            has_schema=bool(schema)
        )

        # If input data is provided, use it; otherwise use default
        if input_data:
            return {"input": input_data}
        elif default_value is not None:
            return {"input": default_value}
        else:
            return {"input": None}


class OutputNodeExecutor(BaseNodeExecutor):
    """Executor for OUTPUT type nodes."""

    async def execute(
        self,
        node: ChainNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute an output node."""
        output_vars = node.config.get("outputs", [])

        self.logger.info(
            "executing_output_node",
            node_id=node.id,
            output_vars=output_vars
        )

        # Collect specified output variables
        output = {}
        for var_name in output_vars:
            if var_name in context.variables:
                output[var_name] = context.variables[var_name]

        return {"output": output}
