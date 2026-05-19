"""
FastAPI router for the tool registry module.

Provides REST API endpoints for tool registration, discovery, and management.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from agent_toolkit.models.adapter_config_models import AdapterConfig
from agent_toolkit.models.shared_api_response_models import APIResponse, Pagination
from agent_toolkit.models.tool_registration_models import ToolRegistration, ToolVersion
from agent_toolkit.models.tool_definition_models import ToolMetadata
from agent_toolkit.observability.rate_limiting_middleware import get_limiter
from agent_toolkit.registry.tool_registry_service import ToolRegistryService

router = APIRouter()
limiter = get_limiter()


# 注意：这些实例由 orchestrator 路由器初始化和管理
# 这里使用占位函数，实际依赖注入由应用入口处理
_registry_service_instance: ToolRegistryService | None = None


def set_registry_service_instance(service: ToolRegistryService) -> None:
    """设置共享的注册服务实例（由 orchestrator 路由器调用）。"""
    global _registry_service_instance
    _registry_service_instance = service


def get_registry_service() -> ToolRegistryService:
    """返回 ToolRegistryService 单例实例（FastAPI 依赖注入）。"""
    global _registry_service_instance
    if _registry_service_instance is None:
        # 延迟初始化：如果没有设置共享实例，创建一个新的
        # 实际应用中应该由 orchestrator 路由器先初始化
        from agent_toolkit.runtime.tool_runtime_service import ToolRuntimeService
        runtime = ToolRuntimeService()
        _registry_service_instance = ToolRegistryService(runtime_service=runtime)
    return _registry_service_instance


class ToolRegistrationRequest(BaseModel):
    """
    工具注册请求模型，合并 metadata 和 adapter_config。

    支持两种格式：
    1. 嵌套格式: {"metadata": {...}, "adapter_config": {"type": "local", ...}}
    2. 扁平格式: {"name": "...", "version": "...", "adapter_type": "local", ...}

    Attributes:
        metadata: Tool metadata (name, description, version, etc.).
        adapter_config: Adapter configuration for the tool.
    """

    metadata: ToolMetadata = Field(..., description="Tool metadata")
    adapter_config: AdapterConfig = Field(..., description="Adapter configuration")

    @model_validator(mode="before")
    @classmethod
    def _normalize_flat_format(cls, data: Any) -> Any:
        """
        将扁平格式的请求数据转换为嵌套格式。

        如果数据中包含 'metadata' 和 'adapter_config' 键，则视为嵌套格式，直接返回。
        否则视为扁平格式，将扁平字段映射到对应的嵌套结构中。
        """
        if not isinstance(data, dict):
            return data

        # 已经是嵌套格式
        if "metadata" in data and "adapter_config" in data:
            return data

        # 扁平格式 -> 嵌套格式
        metadata_keys = {
            "name", "description", "version", "author", "license",
            "category", "tags", "input_schema", "output_schema", "dependencies",
        }
        adapter_keys = {
            "adapter_type", "adapter_endpoint", "auth_config",
            "timeout", "headers",
        }

        metadata_fields = {k: v for k, v in data.items() if k in metadata_keys}
        adapter_fields = {k: v for k, v in data.items() if k in adapter_keys}

        if metadata_fields or adapter_fields:
            normalized: dict[str, Any] = {}

            if metadata_fields:
                normalized["metadata"] = metadata_fields

            if adapter_fields:
                adapter_config = dict(adapter_fields)
                # 将 adapter_type 映射为 type
                if "adapter_type" in adapter_config:
                    adapter_config["type"] = adapter_config.pop("adapter_type")
                if "adapter_endpoint" in adapter_config:
                    adapter_config["endpoint"] = adapter_config.pop("adapter_endpoint")
                # 如果用户也传了 adapter_config 字典，合并进去
                if "adapter_config" in data and isinstance(data["adapter_config"], dict):
                    for k, v in data["adapter_config"].items():
                        if k not in adapter_config:  # adapter_type 优先
                            adapter_config[k] = v
                normalized["adapter_config"] = adapter_config
            elif "adapter_config" in data:
                # 没有 adapter_keys 但有 adapter_config 字段
                normalized["adapter_config"] = data["adapter_config"]

            # 保留不在上述两组中的字段
            for k, v in data.items():
                if k not in metadata_keys and k not in adapter_keys and k != "adapter_config":
                    normalized[k] = v

            return normalized

        return data


@router.post("/tools", response_model=APIResponse[ToolRegistration], status_code=201)
@limiter.limit("100/minute")
async def register_tool(
    request: Request,
    body: ToolRegistrationRequest,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    Register a new tool.

    Args:
        request: 工具注册请求，包含 metadata 和 adapter_config。
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the created ToolRegistration.
    """
    try:
        registration = await service.register_tool(
            metadata=body.metadata,
            adapter_config=body.adapter_config,
        )
        return APIResponse(code=201, message="Tool registered successfully", data=registration)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/tools", response_model=APIResponse[Pagination])
@limiter.limit("100/minute")
async def list_tools(
    request: Request,
    category: Optional[str] = Query(default=None, description="Filter by category"),
    enabled_only: bool = Query(default=True, description="Only show enabled tools"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[Pagination]:
    """
    List registered tools with optional filtering and pagination.

    Args:
        category: Filter by tool category.
        enabled_only: Only return enabled tools.
        page: Page number (1-indexed).
        page_size: Items per page.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with paginated tool list.
    """
    pagination = await service.list_tools(
        category=category,
        enabled_only=enabled_only,
        page=page,
        page_size=page_size,
    )
    return APIResponse(code=200, message="Tools retrieved successfully", data=pagination)


@router.get("/tools/{tool_id}", response_model=APIResponse[ToolRegistration])
async def get_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    Get a tool registration by ID.

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the ToolRegistration.
    """
    registration = await service.get_tool(tool_id)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Tool retrieved successfully", data=registration)


@router.put("/tools/{tool_id}", response_model=APIResponse[ToolRegistration])
async def update_tool(
    tool_id: str,
    updates: dict[str, Any],
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    更新工具元数据或配置。

    Args:
        tool_id: Unique tool identifier.
        updates: 需要更新的字段字典。
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the updated ToolRegistration.
    """
    registration = await service.update_tool(tool_id, updates)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Tool updated successfully", data=registration)


@router.delete("/tools/{tool_id}", response_model=APIResponse)
async def deregister_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse:
    """
    Remove a tool from the registry.

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse confirming deletion.
    """
    deleted = await service.deregister_tool(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message=f"Tool '{tool_id}' deregistered successfully")


@router.post("/tools/{tool_id}/enable", response_model=APIResponse[ToolRegistration])
async def enable_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    Enable a registered tool.

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the updated ToolRegistration.
    """
    registration = await service.enable_tool(tool_id)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Tool enabled", data=registration)


@router.post("/tools/{tool_id}/disable", response_model=APIResponse[ToolRegistration])
async def disable_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    Disable a registered tool.

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the updated ToolRegistration.
    """
    registration = await service.disable_tool(tool_id)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Tool disabled", data=registration)


@router.get("/tools/{tool_id}/versions", response_model=APIResponse[list[ToolVersion]])
async def get_tool_versions(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[list[ToolVersion]]:
    """
    查看工具的版本历史。

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the version history list.
    """
    registration = await service.get_tool(tool_id)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Versions retrieved", data=registration.versions)


@router.get("/tools/name/{name}", response_model=APIResponse[ToolRegistration])
async def get_tool_by_name(
    name: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    按名称查找工具。

    Args:
        name: Tool name.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the ToolRegistration.
    """
    registration = await service.get_tool_by_name(name)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool with name '{name}' not found")
    return APIResponse(code=200, message="Tool retrieved by name", data=registration)


@router.post("/tools/{tool_id}/health", response_model=APIResponse[dict[str, Any]])
async def health_check_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[dict[str, Any]]:
    """
    触发工具健康检查。

    Args:
        tool_id: Unique tool identifier.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with health check result.
    """
    registration = await service.get_tool(tool_id)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    adapter = await service.get_adapter(tool_id)
    if adapter is None:
        return APIResponse(
            code=200,
            message="Health check completed",
            data={"tool_id": tool_id, "status": "unhealthy", "reason": "adapter not available"},
        )

    try:
        # 尝试通过适配器进行健康检查
        healthy = await adapter.health_check() if hasattr(adapter, "health_check") else True
        status = "healthy" if healthy else "unhealthy"
        return APIResponse(
            code=200,
            message="Health check completed",
            data={"tool_id": tool_id, "status": status},
        )
    except (OSError, RuntimeError, ValueError) as exc:
        return APIResponse(
            code=200,
            message="Health check completed",
            data={"tool_id": tool_id, "status": "unhealthy", "reason": str(exc)},
        )


@router.post("/tools/{tool_id}/versions", response_model=APIResponse[ToolRegistration])
async def add_tool_version(
    tool_id: str,
    version: ToolVersion,
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[ToolRegistration]:
    """
    Add a new version to a tool's version history.

    Args:
        tool_id: Unique tool identifier.
        version: Version information.
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with the updated ToolRegistration.
    """
    registration = await service.add_version(tool_id, version)
    if registration is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return APIResponse(code=200, message="Version added", data=registration)


@router.get("/categories", response_model=APIResponse[list[str]])
async def list_categories(
    service: ToolRegistryService = Depends(get_registry_service),
) -> APIResponse[list[str]]:
    """
    List all unique tool categories.

    Args:
        service: 注入的 ToolRegistryService。

    Returns:
        APIResponse with a list of category names.
    """
    categories = await service.get_categories()
    return APIResponse(code=200, message="Categories retrieved", data=categories)
