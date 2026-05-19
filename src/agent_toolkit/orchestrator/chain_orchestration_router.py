"""
FastAPI router for the tool orchestrator module.

Provides REST API endpoints for chain management and execution.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from agent_toolkit.models.shared_api_response_models import APIResponse, Pagination
from agent_toolkit.models.chain_orchestration_models import ChainDefinition, ChainExecution
from agent_toolkit.observability.rate_limiting_middleware import get_limiter
from agent_toolkit.orchestrator.chain_orchestration_service import ToolOrchestratorService
from agent_toolkit.registry.tool_registry_service import ToolRegistryService
from agent_toolkit.runtime.tool_runtime_service import ToolRuntimeService

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = get_limiter()


# 共享的运行时服务实例
_runtime_service_instance: ToolRuntimeService | None = None
_orchestrator_service_instance: ToolOrchestratorService | None = None
_registry_service_instance: ToolRegistryService | None = None


def get_runtime_service() -> ToolRuntimeService:
    """返回共享的 ToolRuntimeService 单例实例。"""
    global _runtime_service_instance
    if _runtime_service_instance is None:
        _runtime_service_instance = ToolRuntimeService()
    return _runtime_service_instance


def get_registry_service() -> ToolRegistryService:
    """返回 ToolRegistryService 单例实例（与注册路由器共享）。"""
    global _registry_service_instance
    if _registry_service_instance is None:
        # 使用共享的运行时服务
        _registry_service_instance = ToolRegistryService(
            runtime_service=get_runtime_service()
        )
    return _registry_service_instance


def get_orchestrator_service() -> ToolOrchestratorService:
    """返回 ToolOrchestratorService 单例实例（FastAPI 依赖注入）。"""
    global _orchestrator_service_instance
    if _orchestrator_service_instance is None:
        # 使用共享的运行时服务和注册服务
        runtime = get_runtime_service()
        registry = get_registry_service()
        _orchestrator_service_instance = ToolOrchestratorService(
            runtime_service=runtime,
            registry_service=registry,
        )
    return _orchestrator_service_instance


@router.post("/chains", response_model=APIResponse[ChainDefinition], status_code=201)
@limiter.limit("100/minute")
async def register_chain(
    request: Request,
    chain: ChainDefinition,
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainDefinition]:
    """
    Register a new tool chain.

    Args:
        chain: Chain definition with nodes and dependencies.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the registered ChainDefinition.
    """
    try:
        registered = await service.register_chain(chain)
        return APIResponse(code=201, message="Chain registered successfully", data=registered)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/chains", response_model=APIResponse[Pagination])
@limiter.limit("100/minute")
async def list_chains(
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[Pagination]:
    """
    List registered chain definitions.

    Args:
        page: Page number.
        page_size: Items per page.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with paginated chain list.
    """
    pagination = await service.list_chains(page=page, page_size=page_size)
    return APIResponse(code=200, message="Chains retrieved", data=pagination)


@router.get("/chains/{chain_name}", response_model=APIResponse[ChainDefinition])
async def get_chain(
    chain_name: str,
    version: str = Query(default="1.0.0", description="Chain version"),
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainDefinition]:
    """
    Get a registered chain definition.

    Args:
        chain_name: Name of the chain.
        version: Chain version.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the ChainDefinition.
    """
    chain = await service.get_chain(chain_name, version)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_name}' version '{version}' not found")
    return APIResponse(code=200, message="Chain retrieved", data=chain)


@router.put("/chains/{chain_name}", response_model=APIResponse[ChainDefinition])
async def update_chain(
    chain_name: str,
    updates: dict[str, Any],
    version: str = Query(default="1.0.0", description="Chain version"),
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainDefinition]:
    """
    更新链定义。

    Args:
        chain_name: Name of the chain.
        updates: 需要更新的字段字典。
        version: Chain version.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the updated ChainDefinition.
    """
    chain = await service.update_chain(chain_name, version, updates)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_name}' version '{version}' not found")
    return APIResponse(code=200, message="Chain updated successfully", data=chain)


@router.delete("/chains/{chain_name}", response_model=APIResponse)
async def delete_chain(
    chain_name: str,
    version: str = Query(default="1.0.0", description="Chain version"),
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse:
    """
    Delete a registered chain definition.

    Args:
        chain_name: Name of the chain.
        version: Chain version.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse confirming deletion.
    """
    deleted = await service.delete_chain(chain_name, version)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_name}' version '{version}' not found")
    return APIResponse(code=200, message=f"Chain '{chain_name}' deleted")


@router.post("/chains/{chain_name}/execute", response_model=APIResponse[ChainExecution])
@limiter.limit("100/minute")
async def execute_chain(
    request: Request,
    chain_name: str,
    version: str = Query(default="1.0.0", description="Chain version"),
    parameters: Optional[dict[str, Any]] = None,
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainExecution]:
    """
    Execute a registered tool chain.

    Args:
        chain_name: Name of the chain to execute.
        version: Chain version.
        parameters: Optional initial parameters for the chain.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the ChainExecution results.
    """
    try:
        execution = await service.execute_chain(
            chain_name=chain_name,
            chain_version=version,
            initial_parameters=parameters,
        )
        return APIResponse(code=200, message="Chain executed", data=execution)
    except ValueError as exc:
        error_msg = str(exc)
        # 区分"链不存在"和"执行时验证错误（如循环依赖）"
        if "not found" in error_msg.lower() or "available" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            # 循环依赖、参数验证等执行时错误返回 422
            raise HTTPException(status_code=422, detail=error_msg)


@router.post("/chains/execute-direct", response_model=APIResponse[ChainExecution])
async def execute_chain_direct(
    chain: ChainDefinition,
    parameters: Optional[dict[str, Any]] = None,
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainExecution]:
    """
    Execute a chain directly without prior registration.

    Args:
        chain: Chain definition to execute.
        parameters: Optional initial parameters for the chain.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the ChainExecution results.
    """
    try:
        execution = await service.execute_chain_direct(chain, parameters)
        return APIResponse(code=200, message="Chain executed", data=execution)
    except ValueError as exc:
        logger.error("Chain validation error: %s", exc)
        raise HTTPException(status_code=400, detail=f"Chain validation failed: {exc}") from exc
    except RuntimeError as exc:
        logger.error("Chain execution error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Chain execution failed: {exc}") from exc


@router.get("/executions/{chain_id}", response_model=APIResponse[ChainExecution])
async def get_chain_execution(
    chain_id: str,
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[ChainExecution]:
    """
    Get the status and results of a chain execution.

    Args:
        chain_id: Unique chain execution identifier.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with the ChainExecution.
    """
    execution = await service.get_execution(chain_id)
    if execution is None:
        raise HTTPException(status_code=404, detail=f"Chain execution '{chain_id}' not found")
    return APIResponse(code=200, message="Execution retrieved", data=execution)


@router.get("/executions", response_model=APIResponse[Pagination])
async def list_chain_executions(
    chain_name: Optional[str] = Query(default=None, description="Filter by chain name"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: ToolOrchestratorService = Depends(get_orchestrator_service),
) -> APIResponse[Pagination]:
    """
    List chain execution history.

    Args:
        chain_name: Filter by chain name.
        status: Filter by execution status.
        page: Page number.
        page_size: Items per page.
        service: 注入的 ToolOrchestratorService。

    Returns:
        APIResponse with paginated execution list.
    """
    pagination = await service.list_executions(
        chain_name=chain_name,
        status=status,
        page=page,
        page_size=page_size,
    )
    return APIResponse(code=200, message="Executions retrieved", data=pagination)
