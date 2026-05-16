"""Flow control operations for tool chains."""

from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from agent_toolkit.orchestrator.orchestration_models import ChainStep, StepResult, ControlFlowType
from agent_toolkit.shared.structured_logging import get_logger


class FlowCondition:
    """Condition for conditional execution."""
    
    def __init__(
        self,
        expression: str,
        evaluator: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        self.expression = expression
        self.evaluator = evaluator or self._default_evaluator
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition."""
        return self.evaluator(context)
    
    def _default_evaluator(self, context: Dict[str, Any]) -> bool:
        """Default condition evaluator."""
        try:
            return eval(self.expression, {"context": context})
        except Exception:
            return False


class ParallelFlow:
    """Parallel execution of steps."""
    
    def __init__(self, steps: List[ChainStep]):
        self.steps = steps
    
    def get_executable_steps(
        self,
        results: Dict[str, StepResult],
    ) -> List[ChainStep]:
        """Get steps ready to execute in parallel."""
        executable = []
        
        for step in self.steps:
            dependencies_met = all(
                results.get(dep_id, StepResult(step_id=dep_id, status="completed")).status == "completed"
                for dep_id in step.depends_on
            )
            
            if dependencies_met:
                executable.append(step)
        
        return executable


class LoopFlow:
    """Loop execution of steps."""
    
    def __init__(
        self,
        steps: List[ChainStep],
        items_path: str,
        max_iterations: int = 100,
    ):
        self.steps = steps
        self.items_path = items_path
        self.max_iterations = max_iterations
    
    def get_iteration_count(self, context: Dict[str, Any]) -> int:
        """Get number of loop iterations."""
        items = self._get_items(context)
        return min(len(items) if items else 0, self.max_iterations)
    
    def _get_items(self, context: Dict[str, Any]) -> List[Any]:
        """Get items to iterate over."""
        parts = self.items_path.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, [])
            else:
                return []
        
        return value if isinstance(value, list) else []


class ConditionalFlow:
    """Conditional execution of steps."""
    
    def __init__(self, condition: FlowCondition):
        self.condition = condition
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if steps should be executed."""
        return self.condition.evaluate(context)


class MapFlow:
    """Map operation over a collection."""
    
    def __init__(
        self,
        step: ChainStep,
        collection_path: str,
    ):
        self.step = step
        self.collection_path = collection_path
    
    def get_collection(self, context: Dict[str, Any]) -> List[Any]:
        """Get collection to map over."""
        parts = self.collection_path.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, [])
            else:
                return []
        
        return value if isinstance(value, list) else []


def create_flow_control(
    flow_type: ControlFlowType,
    steps: List[ChainStep],
    **kwargs,
) -> Any:
    """Factory function to create flow control."""
    if flow_type == ControlFlowType.PARALLEL:
        return ParallelFlow(steps)
    elif flow_type == ControlFlowType.CONDITIONAL:
        condition = FlowCondition(kwargs.get("expression", "True"))
        return ConditionalFlow(condition)
    elif flow_type == ControlFlowType.LOOP:
        return LoopFlow(
            steps,
            items_path=kwargs.get("items_path", "items"),
            max_iterations=kwargs.get("max_iterations", 100),
        )
    elif flow_type == ControlFlowType.MAP:
        return MapFlow(
            steps[0] if steps else None,
            collection_path=kwargs.get("collection_path", "collection"),
        )
    else:
        return None
