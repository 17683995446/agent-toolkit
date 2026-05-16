"""FastAPI routes for Tool Registry."""

from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent_toolkit.shared.database_connection import get_db_session
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError, DuplicateError, ValidationError, AgentToolkitException
)
from agent_toolkit.registry.registry_service import (
    ToolService, ToolVersionService, ToolCategoryService, RegistryStatsService
)
from agent_toolkit.registry.tool_publication_service import (
    ToolPublicationService, PublicationWorkflow
)
from agent_toolkit.registry.tool_validation_service import (
    ToolValidationService, ValidationResult
)
from agent_toolkit.registry.registry_schemas import (
    ToolCreate, ToolUpdate, ToolResponse, ToolListResponse,
    ToolVersionCreate, ToolVersionResponse,
    ToolCategoryCreate, ToolCategoryUpdate, ToolCategoryResponse,
    ToolSearchQuery, ToolStatsResponse, HealthCheckResponse, ErrorResponse
)

router = APIRouter(prefix="/api/v1", tags=["tools"])


async def get_tool_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ToolService:
    """Get ToolService instance."""
    return ToolService(session)


async def get_version_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ToolVersionService:
    """Get ToolVersionService instance."""
    return ToolVersionService(session)


async def get_category_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ToolCategoryService:
    """Get ToolCategoryService instance."""
    return ToolCategoryService(session)


async def get_stats_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> RegistryStatsService:
    """Get RegistryStatsService instance."""
    return RegistryStatsService(session)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Check API health status."""
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        version="0.1.0",
        timestamp=datetime.utcnow()
    )


@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Create a new tool."""
    try:
        tool = await service.create_tool(tool_data)
        return tool
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    service: Annotated[ToolService, Depends(get_tool_service)],
    category_id: Optional[int] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    adapter_type: Optional[str] = Query(None, description="Filter by adapter type"),
    search: Optional[str] = Query(None, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    author: Optional[str] = Query(None, description="Filter by author"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
):
    """List all tools with pagination."""
    tag_list = tags.split(",") if tags else None
    
    tools, total = await service.list_tools(
        page=page,
        page_size=page_size,
        category_id=category_id,
        status=status,
        adapter_type=adapter_type,
        search=search,
        tags=tag_list,
        author=author,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return ToolListResponse(
        items=tools,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Get tool by ID."""
    try:
        tool = await service.get_tool(tool_id)
        return tool
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.get("/tools/name/{name}", response_model=ToolResponse)
async def get_tool_by_name(
    name: str,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Get tool by name."""
    try:
        tool = await service.get_tool_by_name(name)
        return tool
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    update_data: ToolUpdate,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Update a tool."""
    try:
        tool = await service.update_tool(tool_id, update_data)
        return tool
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Delete a tool."""
    try:
        await service.delete_tool(tool_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.post("/tools/{tool_id}/activate", response_model=ToolResponse)
async def activate_tool(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Activate a tool."""
    try:
        tool = await service.activate_tool(tool_id)
        return tool
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.post("/tools/{tool_id}/deprecate", response_model=ToolResponse)
async def deprecate_tool(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Deprecate a tool."""
    try:
        tool = await service.deprecate_tool(tool_id)
        return tool
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.post("/tools/{tool_id}/rate")
async def rate_tool(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)],
    rating: float = Query(..., ge=0, le=5)
):
    """Rate a tool."""
    try:
        await service.rate_tool(tool_id, rating)
        return {"success": True, "tool_id": tool_id, "rating": rating}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.post("/tools/{tool_id}/versions", response_model=ToolVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_version(
    tool_id: int,
    version_data: ToolVersionCreate,
    service: Annotated[ToolVersionService, Depends(get_version_service)]
):
    """Create a new version for a tool."""
    try:
        version = await service.create_version(tool_id, version_data)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.to_dict())


@router.get("/tools/{tool_id}/versions", response_model=list[ToolVersionResponse])
async def list_tool_versions(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)],
    version_service: Annotated[ToolVersionService, Depends(get_version_service)]
):
    """List all versions for a tool."""
    try:
        await service.get_tool(tool_id)
        versions = await version_service.list_versions(tool_id)
        return versions
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.get("/tools/{tool_id}/versions/latest", response_model=ToolVersionResponse)
async def get_latest_version(
    tool_id: int,
    service: Annotated[ToolService, Depends(get_tool_service)],
    version_service: Annotated[ToolVersionService, Depends(get_version_service)]
):
    """Get the latest version for a tool."""
    try:
        await service.get_tool(tool_id)
        version = await version_service.get_latest_version(tool_id)
        return version
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.get("/stats", response_model=ToolStatsResponse)
async def get_stats(
    service: Annotated[RegistryStatsService, Depends(get_stats_service)]
):
    """Get registry statistics."""
    stats = await service.get_stats()
    return ToolStatsResponse(**stats)


categories_router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@categories_router.post("", response_model=ToolCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: ToolCategoryCreate,
    service: Annotated[ToolCategoryService, Depends(get_category_service)]
):
    """Create a new category."""
    try:
        category = await service.create_category(category_data)
        return category
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.to_dict())


@categories_router.get("", response_model=list[ToolCategoryResponse])
async def list_categories(
    service: Annotated[ToolCategoryService, Depends(get_category_service)],
    include_children: bool = Query(False, description="Include child categories")
):
    """List all categories."""
    categories = await service.list_categories(include_children=include_children)
    return categories


@categories_router.get("/{category_id}", response_model=ToolCategoryResponse)
async def get_category(
    category_id: int,
    service: Annotated[ToolCategoryService, Depends(get_category_service)]
):
    """Get category by ID."""
    try:
        category = await service.get_category(category_id)
        return category
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@categories_router.put("/{category_id}", response_model=ToolCategoryResponse)
async def update_category(
    category_id: int,
    update_data: ToolCategoryUpdate,
    service: Annotated[ToolCategoryService, Depends(get_category_service)]
):
    """Update a category."""
    try:
        category = await service.update_category(category_id, update_data)
        return category
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: Annotated[ToolCategoryService, Depends(get_category_service)]
):
    """Delete a category."""
    try:
        await service.delete_category(category_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


async def get_publication_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ToolPublicationService:
    """Get ToolPublicationService instance."""
    return ToolPublicationService(session)


async def get_validation_service() -> ToolValidationService:
    """Get ToolValidationService instance."""
    return ToolValidationService()


@router.post("/tools/{tool_id}/validate")
async def validate_tool_endpoint(
    tool_id: int,
    validation_service: Annotated[ToolValidationService, Depends(get_validation_service)],
    tool_service: Annotated[ToolService, Depends(get_tool_service)]
):
    """Validate a tool."""
    try:
        tool = await tool_service.get_tool(tool_id)
        tool_create = ToolCreate(
            name=tool.name,
            description=tool.description,
            version=tool.version,
            category_id=tool.category_id,
            status=tool.status,
            adapter_type=tool.adapter_type,
            adapter_config=tool.adapter_config,
            input_schema=tool.input_schema,
            output_schema=tool.output_schema,
            metadata=tool.metadata,
            tags=tool.tags,
            author=tool.author,
            license=getattr(tool, 'license', None)
        )
        validation_result = await validation_service.validate_tool(tool_create)
        return {
            "valid": validation_result.valid,
            "issues": [
                {
                    "field": issue.field,
                    "message": issue.message,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion
                }
                for issue in validation_result.issues
            ],
            "warnings": [
                {
                    "field": issue.field,
                    "message": issue.message,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion
                }
                for issue in validation_result.warnings
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.post("/tools/{tool_id}/submit-review")
async def submit_for_review(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    submitter: str,
    notes: Optional[str] = None
):
    """Submit a tool for review."""
    try:
        workflow = await service.submit_for_review(tool_id, submitter, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.post("/tools/{tool_id}/approve")
async def approve_tool(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    reviewer: str,
    notes: Optional[str] = None
):
    """Approve a tool."""
    try:
        workflow = await service.approve(tool_id, reviewer, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.post("/tools/{tool_id}/reject")
async def reject_tool(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    reviewer: str,
    reason: str,
    notes: Optional[str] = None
):
    """Reject a tool."""
    try:
        workflow = await service.reject(tool_id, reviewer, reason, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.post("/tools/{tool_id}/request-revision")
async def request_revision(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    reviewer: str,
    feedback: str,
    notes: Optional[str] = None
):
    """Request revisions for a tool."""
    try:
        workflow = await service.request_revision(tool_id, reviewer, feedback, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.post("/tools/{tool_id}/publish")
async def publish_tool(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    publisher: str,
    notes: Optional[str] = None
):
    """Publish an approved tool."""
    try:
        workflow = await service.publish(tool_id, publisher, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.post("/tools/{tool_id}/unpublish")
async def unpublish_tool(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    actor: str,
    reason: str,
    notes: Optional[str] = None
):
    """Unpublish an active tool."""
    try:
        workflow = await service.unpublish(tool_id, actor, reason, notes)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.to_dict())


@router.get("/tools/{tool_id}/workflow")
async def get_workflow(
    tool_id: int,
    service: Annotated[ToolPublicationService, Depends(get_publication_service)]
):
    """Get the publication workflow for a tool."""
    try:
        workflow = await service.get_workflow(tool_id)
        return {
            "tool_id": workflow.tool_id,
            "current_status": workflow.current_status,
            "status_history": [
                {
                    "action": event.action,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "notes": event.notes
                }
                for event in workflow.status_history
            ]
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.to_dict())


@router.get("/pending-reviews")
async def get_pending_reviews(
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    page: int = 1,
    page_size: int = 20
):
    """Get all tools pending review."""
    tools, total = await service.get_pending_reviews(page, page_size)
    return {
        "tools": [ToolResponse.model_validate(tool).model_dump() for tool in tools],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/published")
async def get_published_tools(
    service: Annotated[ToolPublicationService, Depends(get_publication_service)],
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None
):
    """Get all published (active) tools."""
    tools, total = await service.get_published_tools(page, page_size, category_id)
    return {
        "tools": [ToolResponse.model_validate(tool).model_dump() for tool in tools],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
