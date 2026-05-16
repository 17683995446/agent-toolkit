"""Tool publication service for managing tool review, approval, and publication workflows."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from agent_toolkit.shared.custom_exceptions import (
    NotFoundError, ValidationError, DuplicateError, ForbiddenError
)
# from agent_toolkit.shared.structured_logging import LoggerMixin
from agent_toolkit.registry.registry_models import (
    Tool, ToolStatus, ToolVersion, ToolCategory
)
from agent_toolkit.registry.registry_repository import (
    ToolRepository, ToolVersionRepository, ToolCategoryRepository
)
from agent_toolkit.registry.registry_schemas import (
    ToolCreate, ToolUpdate, ToolVersionCreate
)
from agent_toolkit.registry.tool_validation_service import (
    ToolValidationService, ValidationResult, ValidationIssue, ValidationSeverity
)


class PublicationAction(str, Enum):
    """Publication action types."""
    SUBMIT_FOR_REVIEW = "submit_for_review"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"
    REQUEST_REVISION = "request_revision"


@dataclass
class PublicationEvent:
    """Represents a publication workflow event."""
    action: PublicationAction
    timestamp: datetime
    actor: str
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PublicationWorkflow:
    """Represents a tool's publication workflow state."""
    tool_id: int
    current_status: ToolStatus
    status_history: List[PublicationEvent]
    latest_validation: Optional[ValidationResult] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


class ToolPublicationService:
    """Service for managing tool publication workflows."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool_repo = ToolRepository(session)
        self.version_repo = ToolVersionRepository(session)
        self.validation_service = ToolValidationService()

    async def submit_for_review(
        self,
        tool_id: int,
        submitter: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Submit a tool for review.
        
        Args:
            tool_id: ID of the tool to submit
            submitter: Name of the submitter
            notes: Optional notes for the review
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not valid for submission
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        # Validate tool before submission
        tool_create = ToolCreate(
            name=tool.name,
            description=tool.description,
            version=tool.version,
            category_id=tool.category_id,
            status=ToolStatus.DRAFT,
            adapter_type=tool.adapter_type,
            adapter_config=tool.adapter_config,
            input_schema=tool.input_schema,
            output_schema=tool.output_schema,
            extra_metadata=tool.extra_metadata,
            tags=tool.tags,
            author=tool.author,
            license=getattr(tool, 'license', None)
        )
        
        validation_result = await self.validation_service.validate_tool(tool_create)
        
        if not validation_result.valid:
            error_messages = "\n".join(
                f"- {issue.field}: {issue.message}"
                for issue in validation_result.issues
                if issue.severity == ValidationSeverity.ERROR
            )
            raise ValidationError(
                f"Tool failed validation and cannot be submitted:\n{error_messages}"
            )

        # Update tool status
        await self.tool_repo.update_status(tool_id, ToolStatus.PENDING_REVIEW)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_submitted_for_review",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     submitter=submitter
        # )

        return await self.get_workflow(tool_id)

    async def approve(
        self,
        tool_id: int,
        reviewer: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Approve a tool for publication.
        
        Args:
            tool_id: ID of the tool to approve
            reviewer: Name of the reviewer
            notes: Optional review notes
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not in review status
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        if tool.status != ToolStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot approve tool with status '{tool.status}'. "
                f"Tool must be in '{ToolStatus.PENDING_REVIEW}' status."
            )

        await self.tool_repo.update_status(tool_id, ToolStatus.APPROVED)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_approved",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     reviewer=reviewer
        # )

        return await self.get_workflow(tool_id)

    async def reject(
        self,
        tool_id: int,
        reviewer: str,
        reason: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Reject a tool submission.
        
        Args:
            tool_id: ID of the tool to reject
            reviewer: Name of the reviewer
            reason: Reason for rejection
            notes: Optional additional notes
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not in review status
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        if tool.status != ToolStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot reject tool with status '{tool.status}'. "
                f"Tool must be in '{ToolStatus.PENDING_REVIEW}' status."
            )

        await self.tool_repo.update_status(tool_id, ToolStatus.REJECTED)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_rejected",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     reviewer=reviewer,
        #     reason=reason
        # )

        return await self.get_workflow(tool_id)

    async def request_revision(
        self,
        tool_id: int,
        reviewer: str,
        feedback: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Request revisions for a tool.
        
        Args:
            tool_id: ID of the tool
            reviewer: Name of the reviewer
            feedback: Revision feedback
            notes: Optional additional notes
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not in review status
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        if tool.status != ToolStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot request revisions for tool with status '{tool.status}'. "
                f"Tool must be in '{ToolStatus.PENDING_REVIEW}' status."
            )

        await self.tool_repo.update_status(tool_id, ToolStatus.DRAFT)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_revision_requested",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     reviewer=reviewer
        # )

        return await self.get_workflow(tool_id)

    async def publish(
        self,
        tool_id: int,
        publisher: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Publish an approved tool.
        
        Args:
            tool_id: ID of the tool to publish
            publisher: Name of the publisher
            notes: Optional publication notes
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not approved
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        if tool.status != ToolStatus.APPROVED:
            raise ValidationError(
                f"Cannot publish tool with status '{tool.status}'. "
                f"Tool must be in '{ToolStatus.APPROVED}' status."
            )

        await self.tool_repo.update_status(tool_id, ToolStatus.ACTIVE)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_published",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     publisher=publisher
        # )

        return await self.get_workflow(tool_id)

    async def unpublish(
        self,
        tool_id: int,
        actor: str,
        reason: str,
        notes: Optional[str] = None
    ) -> PublicationWorkflow:
        """
        Unpublish an active tool.
        
        Args:
            tool_id: ID of the tool to unpublish
            actor: Name of the person performing the action
            reason: Reason for unpublishing
            notes: Optional additional notes
            
        Returns:
            Updated publication workflow
            
        Raises:
            NotFoundError: If tool not found
            ValidationError: If tool is not active
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        if tool.status != ToolStatus.ACTIVE:
            raise ValidationError(
                f"Cannot unpublish tool with status '{tool.status}'. "
                f"Tool must be in '{ToolStatus.ACTIVE}' status."
            )

        await self.tool_repo.update_status(tool_id, ToolStatus.DEPRECATED)
        
        await self.session.commit()
        await self.session.refresh(tool)

        # self.logger.info(
        #     "tool_unpublished",
        #     tool_id=tool_id,
        #     tool_name=tool.name,
        #     actor=actor,
        #     reason=reason
        # )

        return await self.get_workflow(tool_id)

    async def get_workflow(self, tool_id: int) -> PublicationWorkflow:
        """
        Get the full publication workflow for a tool.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            PublicationWorkflow object
            
        Raises:
            NotFoundError: If tool not found
        """
        tool = await self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)

        # Build status history
        status_history: List[PublicationEvent] = []
        
        # For now, we'll simulate history based on current status
        # In a real implementation, we'd store these events in a database
        if tool.status == ToolStatus.PENDING_REVIEW:
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.SUBMIT_FOR_REVIEW,
                    timestamp=tool.updated_at,
                    actor=tool.author
                )
            )
        elif tool.status == ToolStatus.APPROVED:
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.SUBMIT_FOR_REVIEW,
                    timestamp=tool.created_at,
                    actor=tool.author
                )
            )
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.APPROVE,
                    timestamp=tool.updated_at,
                    actor="reviewer"
                )
            )
        elif tool.status == ToolStatus.ACTIVE:
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.SUBMIT_FOR_REVIEW,
                    timestamp=tool.created_at,
                    actor=tool.author
                )
            )
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.APPROVE,
                    timestamp=tool.created_at,
                    actor="reviewer"
                )
            )
            status_history.append(
                PublicationEvent(
                    action=PublicationAction.PUBLISH,
                    timestamp=tool.updated_at,
                    actor="publisher"
                )
            )

        return PublicationWorkflow(
            tool_id=tool_id,
            current_status=tool.status,
            status_history=status_history
        )

    async def get_pending_reviews(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Tool], int]:
        """
        Get all tools pending review.
        
        Args:
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple of (tools_list, total_count)
        """
        query = select(Tool).where(Tool.status == ToolStatus.PENDING_REVIEW)
        
        count_query = select("count").select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        query = query.order_by(desc(Tool.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        tools = result.scalars().all()
        
        return list(tools), total

    async def get_published_tools(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None
    ) -> tuple[List[Tool], int]:
        """
        Get all published (active) tools.
        
        Args:
            page: Page number
            page_size: Page size
            category_id: Optional category filter
            
        Returns:
            Tuple of (tools_list, total_count)
        """
        query = select(Tool).where(Tool.status == ToolStatus.ACTIVE)
        
        if category_id:
            query = query.where(Tool.category_id == category_id)
        
        count_query = select("count").select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        query = query.order_by(desc(Tool.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        tools = result.scalars().all()
        
        return list(tools), total

    async def validate_and_create_tool(
        self,
        tool_data: ToolCreate,
        auto_submit: bool = False
    ) -> tuple[Tool, ValidationResult]:
        """
        Validate and create a new tool.
        
        Args:
            tool_data: Tool creation data
            auto_submit: Whether to automatically submit for review after creation
            
        Returns:
            Tuple of (created_tool, validation_result)
        """
        # Validate the tool first
        validation_result = await self.validation_service.validate_tool(tool_data)
        
        if not validation_result.valid and not auto_submit:
            # For DRAFT tools, we allow creation even with warnings
            has_errors = any(
                issue.severity == ValidationSeverity.ERROR
                for issue in validation_result.issues
            )
            if has_errors:
                error_messages = "\n".join(
                    f"- {issue.field}: {issue.message}"
                    for issue in validation_result.issues
                    if issue.severity == ValidationSeverity.ERROR
                )
                raise ValidationError(
                    f"Tool validation failed:\n{error_messages}"
                )
        
        # If auto-submit, set status to DRAFT first
        original_status = tool_data.status
        if auto_submit:
            tool_data.status = ToolStatus.DRAFT
        
        # Create the tool using the repository
        tool_dict = tool_data.model_dump()
        tool = await self.tool_repo.create(tool_dict)
        
        # Create initial version
        await self.version_repo.create({
            "tool_id": tool.id,
            "version": tool.version,
            "changelog": "Initial version",
            "breaking_changes": False
        })
        
        await self.session.commit()
        await self.session.refresh(tool)
        
        # self.logger.info(
        #     "tool_created",
        #     tool_id=tool.id,
        #     tool_name=tool.name,
        #     valid=validation_result.valid
        # )
        
        # Auto-submit if requested
        if auto_submit and validation_result.valid:
            await self.submit_for_review(tool.id, tool.author)
        
        return tool, validation_result
