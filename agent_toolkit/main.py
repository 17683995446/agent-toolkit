"""
Agent Toolkit 主应用 - 统一 FastAPI 应用
整合所有模块的 API 路由
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from agent_toolkit.shared.application_settings import Settings
from agent_toolkit.shared.structured_logging import setup_logging, get_logger
from agent_toolkit.shared.middleware import setup_middlewares
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError, DuplicateError, ValidationError, AgentToolkitException
)

# 导入各模块的路由
from agent_toolkit.registry.registry_api_routes import router as registry_router
from agent_toolkit.adapter.adapter_api_routes import router as adapter_router
from agent_toolkit.runtime.runtime_api_routes import router as runtime_router
from agent_toolkit.orchestrator.orchestrator_api_routes import router as orchestrator_router
from agent_toolkit.observability.observability_api_routes import router as observability_router


def create_app(settings: Settings = None) -> FastAPI:
    """
    创建 FastAPI 应用实例

    Args:
        settings: 配置对象，如果为 None 则使用默认配置

    Returns:
        FastAPI 应用实例
    """
    # 初始化配置
    if settings is None:
        settings = Settings()

    # 初始化日志
    setup_logging(settings.logging)
    logger = get_logger(__name__)
    logger.info("Creating Agent Toolkit application")

    # 创建 FastAPI 应用
    app = FastAPI(
        title="Agent Toolkit",
        description="Multi-agent orchestration and tool management system",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设置自定义中间件
    setup_middlewares(app)

    # 添加 Prometheus 指标端点
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # 全局异常处理器
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        """处理未找到错误"""
        return JSONResponse(
            status_code=404,
            content={
                "error": "NotFound",
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(DuplicateError)
    async def duplicate_exception_handler(request: Request, exc: DuplicateError):
        """处理重复错误"""
        return JSONResponse(
            status_code=409,
            content={
                "error": "DuplicateError",
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """处理验证错误"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(AgentToolkitException)
    async def agent_toolkit_exception_handler(request: Request, exc: AgentToolkitException):
        """处理通用的 AgentToolkit 异常"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "AgentToolkitError",
                "message": exc.message,
                "details": exc.details
            }
        )

    # 注册各模块路由
    app.include_router(registry_router)
    app.include_router(adapter_router)
    app.include_router(runtime_router)
    app.include_router(orchestrator_router)
    app.include_router(observability_router)

    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "service": "Agent Toolkit",
            "version": "0.1.0",
            "status": "healthy",
            "docs": "/docs"
        }

    # 健康检查
    @app.get("/health")
    async def health():
        """健康检查"""
        return {
            "status": "healthy"
        }

    logger.info("Agent Toolkit application created successfully")
    return app


# 全局应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = Settings()
    uvicorn.run(
        "agent_toolkit.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.environment == "development"
    )
