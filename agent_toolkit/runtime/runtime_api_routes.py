"""
Runtime FastAPI 路由 - 运行时管理 API
简化版本，避免不必要的复杂性
"""

from typing import List, Optional, Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agent_toolkit.runtime.base_executor import (
    ExecutionStatus,
    ExecutionResult,
)
from agent_toolkit.shared.structured_logging import LoggerMixin

router = APIRouter(prefix="/api/v1", tags=["runtime"])


class RuntimeService(LoggerMixin):
    """运行时服务 - 简化版本"""
    
    def __init__(self):
        self.executions: Dict[str, ExecutionResult] = {}
    
    async def get_execution_status(self, execution_id: str) -> ExecutionResult:
        """获取执行状态"""
        if execution_id not in self.executions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution '{execution_id}' not found"
            )
        return self.executions[execution_id]
    
    async def list_executions(
        self,
        status_filter: Optional[ExecutionStatus] = None,
        limit: int = 100
    ) -> List[ExecutionResult]:
        """列出执行记录"""
        results = list(self.executions.values())
        if status_filter:
            results = [r for r in results if r.status == status_filter]
        return results[-limit:]


_runtime_service: Optional[RuntimeService] = None


def get_runtime_service() -> RuntimeService:
    """获取运行时服务"""
    global _runtime_service
    if _runtime_service is None:
        _runtime_service = RuntimeService()
    return _runtime_service


@router.get("/runtime/executions/{execution_id}")
async def get_execution_status(
    execution_id: str,
    service: RuntimeService = Depends(get_runtime_service)
):
    """获取执行状态"""
    try:
        result = await service.get_execution_status(execution_id)
        return {
            "success": True,
            "execution_id": result.execution_id,
            "status": result.status.value,
            "data": result.output,
            "exit_code": result.exit_code,
            "execution_time_ms": result.execution_time_ms
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/runtime/executions")
async def list_executions(
    status_filter: Optional[str] = None,
    limit: int = 100,
    service: RuntimeService = Depends(get_runtime_service)
):
    """列出执行记录"""
    try:
        status_enum = None
        if status_filter:
            status_enum = ExecutionStatus(status_filter)
        
        results = await service.list_executions(status_enum, limit)
        return {
            "success": True,
            "data": [
                {
                    "execution_id": r.execution_id,
                    "status": r.status.value,
                    "exit_code": r.exit_code,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in results
            ],
            "total": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/runtime/status")
async def get_runtime_status(
    service: RuntimeService = Depends(get_runtime_service)
):
    """获取运行时状态"""
    try:
        return {
            "success": True,
            "status": "healthy",
            "executor": {
                "type": "simulated",
                "active_executions": len([
                    r for r in service.executions.values()
                    if r.status == ExecutionStatus.RUNNING
                ]),
                "total_executions": len(service.executions)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
