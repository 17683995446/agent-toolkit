"""
Adapter FastAPI 路由 - 适配器管理 API
"""

from typing import List, Optional, Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from agent_toolkit.adapter.base_adapter import (
    BaseAdapter,
    AdapterType,
    AdapterConfig,
    AdapterResult,
    ExecutionStatus,
    ToolMetadata,
)
from agent_toolkit.adapter.adapter_registry import AdapterRegistry, get_adapter_registry
from agent_toolkit.shared.structured_logging import LoggerMixin

router = APIRouter(prefix="/api/v1", tags=["adapters"])


class AdapterService(LoggerMixin):
    """适配器服务"""
    
    def __init__(self, registry: AdapterRegistry):
        self.registry = registry
    
    async def execute_tool(
        self,
        adapter_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """执行工具"""
        adapter = self.registry.get(adapter_name)
        if not adapter:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter '{adapter_name}' not found"
        )
        
        return await adapter.execute(input_data, context)
    
    async def get_adapters(self) -> List[Dict[str, Any]]:
        """获取所有适配器信息"""
        return self.registry.list_adapters()
    
    async def health_check(self, adapter_name: str) -> bool:
        """健康检查"""
        adapter = self.registry.get(adapter_name)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Adapter '{adapter_name}' not found"
            )
        return await adapter.health_check()


def get_adapter_service() -> AdapterService:
    """依赖注入 - 获取适配器服务"""
    registry = get_adapter_registry()
    return AdapterService(registry)


@router.get("/adapters")
async def list_adapters(
    service: AdapterService = Depends(get_adapter_service)
):
    """列出所有适配器"""
    try:
        adapters = await service.get_adapters()
        return {
            "success": True,
            "data": adapters,
            "total": len(adapters)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/adapters/{adapter_name}")
async def get_adapter_info(
    adapter_name: str,
    service: AdapterService = Depends(get_adapter_service)
):
    """获取适配器详情"""
    try:
        adapters = await service.get_adapters()
        for adapter_info in adapters:
            if adapter_info.get("name") == adapter_name:
                return {
                    "success": True,
                    "data": adapter_info
                }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter '{adapter_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/adapters/{adapter_name}/execute")
async def execute_adapter(
    adapter_name: str,
    input_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    service: AdapterService = Depends(get_adapter_service)
):
    """执行适配器"""
    try:
        result = await service.execute_tool(adapter_name, input_data, context)
        return {
            "success": result.is_success,
            "status": result.status.value,
            "data": result.data,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/adapters/{adapter_name}/health")
async def adapter_health_check(
    adapter_name: str,
    service: AdapterService = Depends(get_adapter_service)
):
    """适配器健康检查"""
    try:
        is_healthy = await service.health_check(adapter_name)
        return {
            "success": True,
            "healthy": is_healthy
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/adapters/types")
async def get_adapter_types():
    """获取支持的适配器类型"""
    return {
        "success": True,
        "types": [t.value for t in AdapterType]
    }
