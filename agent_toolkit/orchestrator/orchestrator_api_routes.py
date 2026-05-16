"""FastAPI routes for orchestrator."""

from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent_toolkit.shared.api_response import APIResponse
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
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
from agent_toolkit.orchestrator.node_executors import (
    ToolNodeExecutor,
    ConditionNodeExecutor,
    LoopNodeExecutor,
    ParallelNodeExecutor,
    MergeNodeExecutor,
    InputNodeExecutor,
    OutputNodeExecutor,
)
from agent_toolkit.shared.structured_logging import LoggerMixin


# In-memory storage for tool chains (in production, use a database)
_chain_storage: dict[str, ToolChain] = {}
_orchestration_engine: OrchestrationEngine | None = None


def get_orchestration_engine() -> OrchestrationEngine:
    """Get or create the orchestration engine."""
    global _orchestration_engine
    if _orchestration_engine is None:
        _orchestration_engine = OrchestrationEngine()
        
        # Register default node executors
        _orchestration_engine.register_node_executor(
            NodeType.TOOL, 
            ToolNodeExecutor(None)  # TODO: Pass actual tool registry
        )
        _orchestration_engine.register_node_executor(
            NodeType.CONDITION, 
            ConditionNodeExecutor()
        )
        _orchestration_engine.register_node_executor(
            NodeType.LOOP, 
            LoopNodeExecutor()
        )
        _orchestration_engine.register_node_executor(
            NodeType.PARALLEL, 
            ParallelNodeExecutor()
        )
        _orchestration_engine.register_node_executor(
            NodeType.MERGE, 
            MergeNodeExecutor()
        )
        _orchestration_engine.register_node_executor(
            NodeType.INPUT, 
            InputNodeExecutor()
        )
        _orchestration_engine.register_node_executor(
            NodeType.OUTPUT, 
            OutputNodeExecutor()
        )
    
    return _orchestration_engine


router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])


class CreateChainRequest(BaseModel):
    """Request to create a tool chain."""
    id: str = Field(..., description="Chain ID")
    name: str = Field(..., description="Chain name")
    description: Optional[str] = Field(None, description="Chain description")
    version: str = Field("1.0.0", description="Chain version")
    nodes: List[ChainNode] = Field(default_factory=list, description="Chain nodes")
    edges: List = Field(default_factory=list, description="Chain edges")
    execution_mode: ExecutionMode = Field(ExecutionMode.SEQUENTIAL, description="Execution mode")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class UpdateChainRequest(BaseModel):
    """Request to update a tool chain."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    nodes: Optional[List[ChainNode]] = None
    edges: Optional[List] = None
    execution_mode: Optional[ExecutionMode] = None
    metadata: Optional[dict] = None


class ExecuteChainRequest(BaseModel):
    """Request to execute a tool chain."""
    initial_inputs: dict = Field(default_factory=dict, description="Initial input variables")
    context_metadata: Optional[dict] = Field(None, description="Execution context metadata")


@router.get("/chains", response_model=APIResponse)
async def list_chains(
    status_filter: Optional[ChainStatus] = Query(None, description="Filter by chain status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
):
    """List all tool chains."""
    all_chains = list(_chain_storage.values())
    
    if status_filter:
        all_chains = [c for c in all_chains if c.status == status_filter]
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_chains = all_chains[start:end]
    
    return APIResponse.success(
        data={
            "chains": [c.model_dump() for c in paginated_chains],
            "total": len(all_chains),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(all_chains) + page_size - 1) // page_size
        },
        message="Chains listed successfully"
    )


@router.get("/chains/{chain_id}", response_model=APIResponse)
async def get_chain(chain_id: str):
    """Get a tool chain by ID."""
    chain = _chain_storage.get(chain_id)
    if not chain:
        return APIResponse.error(
            error_code="CHAIN_NOT_FOUND",
            message=f"Chain not found: {chain_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return APIResponse.success(
        data=chain.model_dump(),
        message="Chain retrieved successfully"
    )


@router.post("/chains", response_model=APIResponse)
async def create_chain(
    request: CreateChainRequest,
):
    """Create a new tool chain."""
    if request.id in _chain_storage:
        return APIResponse.error(
            error_code="CHAIN_ALREADY_EXISTS",
            message=f"Chain already exists: {request.id}",
            status_code=status.HTTP_409_CONFLICT
        )
    
    chain = ToolChain(
        id=request.id,
        name=request.name,
        description=request.description,
        version=request.version,
        nodes=request.nodes,
        edges=request.edges,
        execution_mode=request.execution_mode,
        metadata=request.metadata,
        status=ChainStatus.DRAFT,
    )
    
    # Validate the chain
    is_valid, errors = chain.validate()
    if not is_valid:
        return APIResponse.error(
            error_code="INVALID_CHAIN",
            message="Invalid chain configuration",
            details={"errors": errors},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    _chain_storage[chain.id] = chain
    
    return APIResponse.success(
        data=chain.model_dump(),
        message="Chain created successfully"
    )


@router.put("/chains/{chain_id}", response_model=APIResponse)
async def update_chain(
    chain_id: str,
    request: UpdateChainRequest,
):
    """Update an existing tool chain."""
    chain = _chain_storage.get(chain_id)
    if not chain:
        return APIResponse.error(
            error_code="CHAIN_NOT_FOUND",
            message=f"Chain not found: {chain_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Update fields
    if request.name is not None:
        chain.name = request.name
    if request.description is not None:
        chain.description = request.description
    if request.version is not None:
        chain.version = request.version
    if request.nodes is not None:
        chain.nodes = request.nodes
    if request.edges is not None:
        chain.edges = request.edges
    if request.execution_mode is not None:
        chain.execution_mode = request.execution_mode
    if request.metadata is not None:
        chain.metadata = request.metadata
    
    chain.updated_at = datetime.utcnow()
    
    # Re-validate the chain
    is_valid, errors = chain.validate()
    if not is_valid:
        return APIResponse.error(
            error_code="INVALID_CHAIN",
            message="Invalid chain configuration",
            details={"errors": errors},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    return APIResponse.success(
        data=chain.model_dump(),
        message="Chain updated successfully"
    )


@router.delete("/chains/{chain_id}", response_model=APIResponse)
async def delete_chain(chain_id: str):
    """Delete a tool chain."""
    if chain_id not in _chain_storage:
        return APIResponse.error(
            error_code="CHAIN_NOT_FOUND",
            message=f"Chain not found: {chain_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    del _chain_storage[chain_id]
    
    return APIResponse.success(
        data={"chain_id": chain_id},
        message="Chain deleted successfully"
    )


@router.post("/chains/{chain_id}/execute", response_model=APIResponse)
async def execute_chain(
    chain_id: str,
    request: ExecuteChainRequest,
    engine: Annotated[OrchestrationEngine, Depends(get_orchestration_engine)],
):
    """Execute a tool chain."""
    chain = _chain_storage.get(chain_id)
    if not chain:
        return APIResponse.error(
            error_code="CHAIN_NOT_FOUND",
            message=f"Chain not found: {chain_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        context = await engine.execute_chain(
            chain,
            request.initial_inputs,
            request.context_metadata
        )
        
        # Convert context to serializable dict
        context_dict = {
            "execution_id": context.execution_id,
            "chain_id": context.chain_id,
            "status": context.status.value,
            "node_results": {
                k: (v.model_dump() if hasattr(v, 'model_dump') else v)
                for k, v in context.node_results.items()
            },
            "variables": context.variables,
            "errors": context.errors,
            "start_time": context.start_time.isoformat(),
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "metadata": context.metadata
        }
        
        if context.status == ChainStatus.COMPLETED:
            return APIResponse.success(
                data=context_dict,
                message="Chain executed successfully"
            )
        else:
            return APIResponse.error(
                error_code="CHAIN_EXECUTION_FAILED",
                message=f"Chain execution failed with status: {context.status.value}",
                details=context_dict,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        return APIResponse.error(
            error_code="EXECUTION_ERROR",
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/executions/{execution_id}", response_model=APIResponse)
async def get_execution(
    execution_id: str,
    engine: Annotated[OrchestrationEngine, Depends(get_orchestration_engine)],
):
    """Get an execution context."""
    context = engine.get_execution(execution_id)
    if not context:
        return APIResponse.error(
            error_code="EXECUTION_NOT_FOUND",
            message=f"Execution not found: {execution_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Convert context to serializable dict
    context_dict = {
        "execution_id": context.execution_id,
        "chain_id": context.chain_id,
        "status": context.status.value,
        "node_results": {
            k: (v.model_dump() if hasattr(v, 'model_dump') else v)
            for k, v in context.node_results.items()
        },
        "variables": context.variables,
        "errors": context.errors,
        "start_time": context.start_time.isoformat(),
        "end_time": context.end_time.isoformat() if context.end_time else None,
        "metadata": context.metadata
    }
    
    return APIResponse.success(
        data=context_dict,
        message="Execution retrieved successfully"
    )


@router.post("/executions/{execution_id}/cancel", response_model=APIResponse)
async def cancel_execution(
    execution_id: str,
    engine: Annotated[OrchestrationEngine, Depends(get_orchestration_engine)],
):
    """Cancel an ongoing execution."""
    success = engine.cancel_execution(execution_id)
    
    if success:
        return APIResponse.success(
            data={"execution_id": execution_id},
            message="Execution cancelled successfully"
        )
    else:
        return APIResponse.error(
            error_code="EXECUTION_NOT_FOUND",
            message=f"Execution not found or already completed: {execution_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/executions", response_model=APIResponse)
async def list_executions(
    engine: Annotated[OrchestrationEngine, Depends(get_orchestration_engine)],
):
    """List all active executions."""
    execution_ids = engine.list_active_executions()
    
    return APIResponse.success(
        data={"execution_ids": execution_ids, "count": len(execution_ids)},
        message="Active executions listed successfully"
    )


@router.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    return APIResponse.success(
        data={
            "status": "healthy",
            "engine_initialized": _orchestration_engine is not None,
            "active_chains": len(_chain_storage),
        },
        message="Orchestrator is healthy"
    )
