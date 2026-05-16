"""Docker executor implementation for tool runtime."""

import asyncio
import json
import uuid
from typing import Any, Optional, Dict
from dataclasses import dataclass

try:
    import docker
    from docker.models.containers import Container
    from docker.errors import DockerException, NotFound
    HAS_DOCKER = True
except ImportError:
    docker = None
    Container = None
    DockerException = Exception
    NotFound = Exception
    HAS_DOCKER = False

from agent_toolkit.runtime.base_executor import (
    BaseExecutor,
    ExecutorConfig,
    ExecutionResult,
    ExecutionStatus,
)
from agent_toolkit.shared.structured_logging import LoggerMixin
from agent_toolkit.shared.application_settings import get_settings


@dataclass
class DockerExecutorConfig(ExecutorConfig):
    """Configuration for Docker executor."""
    image: str = "python:3.12-slim"
    docker_host: str = "unix:///var/run/docker.sock"
    network: Optional[str] = None
    volumes: Dict[str, Dict[str, str]] = None
    working_dir: str = "/workspace"
    auto_remove: bool = True
    user: Optional[str] = None


class DockerExecutor(BaseExecutor, LoggerMixin):
    """Executor that runs tools in Docker containers."""

    def __init__(self, config: DockerExecutorConfig):
        super().__init__(config)
        self._docker_client: Optional[docker.DockerClient] = None
        self._config = config

    async def initialize(self) -> None:
        """Initialize Docker client."""
        if self._is_initialized:
            return

        try:
            self._docker_client = docker.DockerClient(
                base_url=self._config.docker_host
            )
            self._docker_client.ping()
            
            await super().initialize()
            
            self.logger.info(
                "docker_executor_initialized",
                docker_host=self._config.docker_host
            )
        except DockerException as e:
            self.logger.error("docker_connection_failed", error=str(e))
            raise

    async def _do_execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute tool in Docker container."""
        if not self._docker_client:
            raise RuntimeError("Docker client not initialized")

        container_id = None
        try:
            container_id = await self._create_container(tool_id, input_data, context)
            
            container = self._docker_client.containers.get(container_id)
            
            await self._run_container(container)

            result = await self._get_container_result(container)

            self.logger.info(
                "docker_execution_completed",
                container_id=container_id,
                exit_code=result.exit_code
            )

            return result

        except Exception as e:
            self.logger.error("docker_execution_failed", error=str(e))
            raise

        finally:
            if container_id and self._config.auto_remove:
                try:
                    container = self._docker_client.containers.get(container_id)
                    container.remove(force=True)
                    self.logger.debug("container_removed", container_id=container_id)
                except Exception as e:
                    self.logger.warning("container_removal_failed", error=str(e))

    async def _create_container(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create a Docker container for execution."""
        env = dict(self._config.environment)
        env.update({
            "TOOL_ID": tool_id,
            "TOOL_INPUT": json.dumps(input_data),
        })

        if context:
            env["EXECUTION_CONTEXT"] = json.dumps(context)

        volumes = {}
        if self._config.volumes:
            for host_path, config in self._config.volumes.items():
                volumes[host_path] = config

        host_config = {
            "auto_remove": self._config.auto_remove,
            "network_mode": self._config.network or "bridge",
        }

        if self._config.user:
            host_config["userns_mode"] = self._config.user

        mem_limit = self._config.memory_limit
        cpu_limit = float(self._config.cpu_limit)

        container = await asyncio.to_thread(
            lambda: self._docker_client.containers.run(
                image=self._config.image,
                command=self._build_command(tool_id, input_data),
                detach=True,
                environment=env,
                volumes=volumes,
                working_dir=self._config.working_dir,
                mem_limit=mem_limit,
                nano_cpus=int(cpu_limit * 1e9),
                **host_config
            )
        )

        self.logger.info(
            "docker_container_created",
            container_id=container.id,
            tool_id=tool_id
        )

        return container.id

    async def _run_container(self, container: Container) -> None:
        """Run container and wait for completion."""
        await asyncio.to_thread(container.wait)
        self.logger.debug("container_finished", container_id=container.id)

    async def _get_container_result(
        self,
        container: Container
    ) -> ExecutionResult:
        """Get execution result from container."""
        logs = await asyncio.to_thread(
            lambda: container.logs(stdout=True, stderr=True).decode("utf-8")
        )

        exit_code = await asyncio.to_thread(lambda: container.wait())

        result = ExecutionResult(
            execution_id=container.id[:12],
            tool_id="",
            status=ExecutionStatus.SUCCESS if exit_code == 0 else ExecutionStatus.FAILED,
            output={"logs": logs},
            exit_code=exit_code,
            metadata={
                "container_id": container.id,
                "image": self._config.image,
            }
        )

        return result

    def _build_command(self, tool_id: str, input_data: Dict[str, Any]) -> str:
        """Build command to execute in container."""
        return f"echo 'Executing tool {tool_id}' && echo '{json.dumps(input_data)}'"

    async def health_check(self) -> bool:
        """Check Docker health."""
        if not self._docker_client:
            return False
        try:
            self._docker_client.ping()
            return True
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup Docker resources."""
        if self._docker_client:
            try:
                self._docker_client.close()
            except Exception as e:
                self.logger.warning("docker_cleanup_failed", error=str(e))
        
        await super().cleanup()

    async def list_containers(self) -> list[Dict[str, Any]]:
        """List running containers."""
        if not self._docker_client:
            return []
        
        containers = await asyncio.to_thread(
            lambda: self._docker_client.containers.list()
        )
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            }
            for c in containers
        ]

    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container."""
        if not self._docker_client:
            return False
        
        try:
            container = self._docker_client.containers.get(container_id)
            await asyncio.to_thread(container.stop, timeout=timeout)
            return True
        except NotFound:
            return False
