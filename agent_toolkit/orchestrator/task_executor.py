"""Executor for running tool chains."""

from typing import Any, Dict, Optional
import asyncio

from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainExecution,
    ChainStep,
    ChainStatus,
    StepStatus,
    StepResult,
)
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
from agent_toolkit.shared.structured_logging import get_logger


class ChainExecutor:
    """Executes tool chains with retry and error handling."""
    
    def __init__(
        self,
        engine: Optional[OrchestrationEngine] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.engine = engine or OrchestrationEngine()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger("orchestrator.executor")
    
    async def execute(
        self,
        chain: ToolChain,
        input_data: Dict[str, Any],
    ) -> ChainExecution:
        """Execute a chain with error handling."""
        execution = await self.engine.create_execution(chain, input_data)
        
        try:
            return await self.engine.execute_chain(chain, input_data)
        except Exception as e:
            execution.status = ChainStatus.FAILED
            execution.error = str(e)
            self.logger.error("chain_execution_error", error=str(e))
            return execution
    
    async def execute_with_retry(
        self,
        chain: ToolChain,
        input_data: Dict[str, Any],
    ) -> ChainExecution:
        """Execute a chain with automatic retry on failure."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                execution = await self.execute(chain, input_data)
                
                if execution.status == ChainStatus.COMPLETED:
                    return execution
                
                last_error = execution.error
            
            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    error=str(e)
                )
            
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return ChainExecution(
            chain_id=chain.chain_id,
            status=ChainStatus.FAILED,
            error=f"Failed after {self.max_retries + 1} attempts: {last_error}",
        )
    
    async def execute_parallel(
        self,
        chains: list[ToolChain],
        input_data: Dict[str, Any],
    ) -> list[ChainExecution]:
        """Execute multiple chains in parallel."""
        tasks = [
            self.execute(chain, input_data)
            for chain in chains
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def validate_chain(self, chain: ToolChain) -> tuple[bool, list[str]]:
        """Validate a chain before execution."""
        errors = []
        
        if not chain.steps:
            errors.append("Chain must have at least one step")
        
        step_ids = {step.step_id for step in chain.steps}
        
        for step in chain.steps:
            if not step.tool_name:
                errors.append(f"Step {step.step_id} has no tool specified")
            
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    errors.append(f"Step {step.step_id} depends on unknown step {dep_id}")
        
        return len(errors) == 0, errors
