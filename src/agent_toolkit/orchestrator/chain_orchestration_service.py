"""
Tool orchestrator service.

Business logic for managing tool chains, including chain registration,
execution management, and result retrieval.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from agent_toolkit.models.shared_api_response_models import APIResponse, Pagination
from agent_toolkit.models.chain_orchestration_models import ChainDefinition, ChainExecution
from agent_toolkit.models.runtime_execution_models import ExecutionStatus
from agent_toolkit.orchestrator.chain_execution_engine import ChainExecutionEngine
from agent_toolkit.registry.tool_registry_service import ToolRegistryService
from agent_toolkit.runtime.tool_runtime_service import ToolRuntimeService
from agent_toolkit.tools.base_tool_definition import BaseTool

logger = logging.getLogger(__name__)


class ToolOrchestratorService:
    """
    Service for managing tool chain orchestration.

    Handles chain registration, execution, monitoring, and result retrieval.
    """

    # 内存中最多保留的执行记录数量
    MAX_EXECUTIONS: int = 5000
    # 执行记录的存活时间（秒），默认 2 小时
    EXECUTION_TTL_SECONDS: int = 7200

    def __init__(
        self,
        runtime_service: ToolRuntimeService | None = None,
        registry_service: ToolRegistryService | None = None,
    ) -> None:
        """
        Initialize the orchestrator service.

        Args:
            runtime_service: Runtime service for executing individual tools.
            registry_service: Registry service for looking up tool definitions.
        """
        self._runtime = runtime_service or ToolRuntimeService()
        self._registry = registry_service or ToolRegistryService()
        self._engine = ChainExecutionEngine(self._runtime)
        self._chains: dict[str, ChainDefinition] = {}
        self._executions: dict[str, ChainExecution] = {}
        # 并发锁，保护共享状态
        self._lock = asyncio.Lock()

    def _cleanup_old_executions(self) -> None:
        """
        清理过期的链执行记录。

        当执行记录数量超过 MAX_EXECUTIONS 时，删除最旧的记录；
        同时删除超过 EXECUTION_TTL_SECONDS 的记录。
        """
        now = datetime.now(timezone.utc)

        # 先清理超过 TTL 的记录
        expired_ids = [
            cid for cid, execution in self._executions.items()
            if execution.started_at is not None
            and (now - execution.started_at).total_seconds()
            > self.EXECUTION_TTL_SECONDS
        ]
        for cid in expired_ids:
            del self._executions[cid]

        # 如果仍然超过限制，按时间排序删除最旧的记录
        if len(self._executions) > self.MAX_EXECUTIONS:
            sorted_ids = sorted(
                self._executions.keys(),
                key=lambda cid: self._executions[cid].started_at or datetime.min.replace(tzinfo=timezone.utc),
            )
            remove_count = len(self._executions) - self.MAX_EXECUTIONS
            for cid in sorted_ids[:remove_count]:
                del self._executions[cid]

        if expired_ids or len(self._executions) > self.MAX_EXECUTIONS:
            logger.info(
                "Orchestrator: 清理执行记录完成，当前记录数: %d",
                len(self._executions),
            )

    async def register_chain(self, chain: ChainDefinition) -> ChainDefinition:
        """
        Register a tool chain definition.

        Args:
            chain: Chain definition with nodes and dependencies.

        Returns:
            The registered ChainDefinition.

        Raises:
            ValueError: If a chain with the same name and version already exists.
        """
        async with self._lock:
            chain_key = f"{chain.name}:{chain.version}"
            if chain_key in self._chains:
                raise ValueError(f"Chain '{chain.name}' version '{chain.version}' already exists")

            self._chains[chain_key] = chain
            logger.info("Registered chain: %s (v%s, %d nodes)", chain.name, chain.version, len(chain.nodes))
            return chain

    async def execute_chain(
        self,
        chain_name: str,
        chain_version: str = "1.0.0",
        initial_parameters: dict[str, Any] | None = None,
    ) -> ChainExecution:
        """
        Execute a registered tool chain.

        Args:
            chain_name: Name of the chain to execute.
            chain_version: Version of the chain (default: "1.0.0").
            initial_parameters: Initial parameters for the chain.

        Returns:
            ChainExecution with per-node results.

        Raises:
            ValueError: If the chain is not found.
        """
        async with self._lock:
            chain_key = f"{chain_name}:{chain_version}"
            chain = self._chains.get(chain_key)
            if chain is None:
                available = list(self._chains.keys())
                raise ValueError(f"Chain '{chain_key}' not found. Available: {available}")

        execution = await self._engine.execute_chain(chain, initial_parameters)

        async with self._lock:
            self._executions[execution.chain_id] = execution
            self._cleanup_old_executions()

        return execution

    async def execute_chain_direct(
        self,
        chain: ChainDefinition,
        initial_parameters: dict[str, Any] | None = None,
    ) -> ChainExecution:
        """
        Execute a chain directly without prior registration.

        Args:
            chain: Chain definition to execute.
            initial_parameters: Initial parameters for the chain.

        Returns:
            ChainExecution with per-node results.
        """
        execution = await self._engine.execute_chain(chain, initial_parameters)

        async with self._lock:
            self._executions[execution.chain_id] = execution
            self._cleanup_old_executions()

        return execution

    async def get_execution(self, chain_id: str) -> Optional[ChainExecution]:
        """
        Get the status and results of a chain execution.

        Args:
            chain_id: Unique chain execution identifier.

        Returns:
            ChainExecution if found, None otherwise.
        """
        return self._executions.get(chain_id)

    async def list_executions(
        self,
        chain_name: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Pagination:
        """
        List chain execution history with optional filtering.

        Args:
            chain_name: Filter by chain name.
            status: Filter by execution status.
            page: Page number.
            page_size: Items per page.

        Returns:
            Pagination with execution records.
        """
        results = list(self._executions.values())

        if chain_name:
            results = [e for e in results if e.chain_name == chain_name]

        if status:
            results = [e for e in results if e.status.value == status]

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return Pagination(
            page=page,
            page_size=page_size,
            total=total,
            items=[e.model_dump() for e in paginated],
        )

    async def list_chains(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Pagination:
        """
        List registered chain definitions.

        Args:
            page: Page number.
            page_size: Items per page.

        Returns:
            Pagination with chain definitions.
        """
        all_chains = list(self._chains.values())
        total = len(all_chains)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_chains[start:end]

        return Pagination(
            page=page,
            page_size=page_size,
            total=total,
            items=[c.model_dump() for c in paginated],
        )

    async def get_chain(self, chain_name: str, chain_version: str = "1.0.0") -> Optional[ChainDefinition]:
        """
        Get a registered chain definition.

        Args:
            chain_name: Name of the chain.
            chain_version: Version of the chain.

        Returns:
            ChainDefinition if found, None otherwise.
        """
        chain_key = f"{chain_name}:{chain_version}"
        return self._chains.get(chain_key)

    async def delete_chain(self, chain_name: str, chain_version: str = "1.0.0") -> bool:
        """
        Delete a registered chain definition.

        删除前会检查是否有正在执行中的链引用该 chain_name，
        如果有活跃执行，将返回 False 并记录警告日志。

        Args:
            chain_name: Name of the chain.
            chain_version: Version of the chain.

        Returns:
            True if the chain was found and deleted.
        """
        async with self._lock:
            chain_key = f"{chain_name}:{chain_version}"
            if chain_key not in self._chains:
                return False

            # 检查是否有正在执行中的链引用该 chain_name
            active_executions = [
                cid for cid, execution in self._executions.items()
                if execution.chain_name == chain_name
                and execution.status == ExecutionStatus.RUNNING
            ]
            if active_executions:
                logger.warning(
                    "无法删除链 '%s'：存在 %d 个活跃执行 (%s)",
                    chain_key,
                    len(active_executions),
                    active_executions,
                )
                return False

            del self._chains[chain_key]
            logger.info("Deleted chain: %s", chain_key)
            return True

    async def update_chain(
        self,
        chain_name: str,
        chain_version: str,
        updates: dict[str, Any],
    ) -> Optional[ChainDefinition]:
        """
        更新已注册的链定义。

        Args:
            chain_name: Name of the chain.
            chain_version: Version of the chain.
            updates: 需要更新的字段字典（如 description、nodes 等）。

        Returns:
            更新后的 ChainDefinition，如果未找到则返回 None。
        """
        async with self._lock:
            chain_key = f"{chain_name}:{chain_version}"
            chain = self._chains.get(chain_key)
            if chain is None:
                return None

            for key, value in updates.items():
                if hasattr(chain, key):
                    setattr(chain, key, value)

            logger.info("Updated chain: %s", chain_key)
            return chain
