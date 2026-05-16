"""CLI Adapter implementation."""

import asyncio
import os
import signal
from typing import Any, Optional, Dict, List
from dataclasses import dataclass

from pydantic import BaseModel, Field

from agent_toolkit.adapter.base_adapter import (
    BaseAdapter,
    AdapterType,
    AdapterConfig,
    AdapterResult,
    ToolMetadata,
    ExecutionStatus,
)
from agent_toolkit.shared.structured_logging import LoggerMixin


class CLIAdapterConfig(BaseModel):
    """Configuration for CLI adapter."""
    command: str = Field(..., description="Command to execute")
    working_dir: Optional[str] = Field(None, description="Working directory")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: int = Field(30, ge=1, description="Execution timeout in seconds")
    shell: bool = Field(True, description="Execute via shell")
    shell_path: str = Field("/bin/sh", description="Shell executable path")
    capture_output: bool = Field(True, description="Capture stdout/stderr")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input JSON schema")


@dataclass
class CLIExecutionResult:
    """Result of CLI execution."""
    stdout: str
    stderr: str
    returncode: int
    execution_time_ms: float


class CLIAdapter(BaseAdapter, LoggerMixin):
    """Adapter for command-line interface tools."""

    def __init__(
        self,
        config: CLIAdapterConfig,
        metadata: Optional[ToolMetadata] = None,
    ):
        self._config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        super().__init__(config=config, metadata=metadata)

    @property
    def adapter_type(self) -> AdapterType:
        """Get adapter type."""
        return AdapterType.CLI

    async def initialize(self) -> None:
        """Initialize the CLI adapter."""
        if self._config.working_dir:
            os.makedirs(self._config.working_dir, exist_ok=True)

        self.logger.info(
            "cli_adapter_initialized",
            command=self._config.command,
            working_dir=self._config.working_dir
        )

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute CLI command."""
        import time
        start_time = time.time()

        try:
            command = self._build_command(input_data)
            env = self._build_environment()
            cwd = self._config.working_dir or os.getcwd()

            self.logger.debug(
                "cli_execution_start",
                command=command,
                cwd=cwd
            )

            if self._config.shell:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE if self._config.capture_output else None,
                    stderr=asyncio.subprocess.PIPE if self._config.capture_output else None,
                    env=env,
                    cwd=cwd,
                    preexec_fn=os.setsid if os.name != 'nt' else None,
                )
            else:
                cmd_parts = command.split()
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    stdout=asyncio.subprocess.PIPE if self._config.capture_output else None,
                    stderr=asyncio.subprocess.PIPE if self._config.capture_output else None,
                    env=env,
                    cwd=cwd,
                    preexec_fn=os.setsid if os.name != 'nt' else None,
                )

            self._process = process

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._config.timeout
                )

                execution_time = (time.time() - start_time) * 1000

                stdout = stdout_data.decode() if stdout_data else ""
                stderr = stderr_data.decode() if stderr_data else ""

                self.logger.info(
                    "cli_execution_complete",
                    returncode=process.returncode,
                    execution_time_ms=execution_time
                )

                if process.returncode == 0:
                    return AdapterResult(
                        status=ExecutionStatus.SUCCESS,
                        data={
                            "stdout": stdout,
                            "stderr": stderr,
                            "returncode": process.returncode,
                        },
                        execution_time_ms=execution_time,
                    )
                else:
                    return AdapterResult(
                        status=ExecutionStatus.FAILURE,
                        data={
                            "stdout": stdout,
                            "stderr": stderr,
                            "returncode": process.returncode,
                        },
                        error=stderr or f"Command failed with exit code {process.returncode}",
                        execution_time_ms=execution_time,
                    )

            except asyncio.TimeoutError:
                execution_time = (time.time() - start_time) * 1000
                await self._terminate_process()
                
                self.logger.warning(
                    "cli_execution_timeout",
                    timeout=self._config.timeout
                )
                
                return AdapterResult(
                    status=ExecutionStatus.TIMEOUT,
                    error=f"Command timed out after {self._config.timeout}s",
                    execution_time_ms=execution_time,
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error("cli_execution_error", error=str(e))
            
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=str(e),
                execution_time_ms=execution_time,
            )
        finally:
            self._process = None

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        if not self._config.input_schema:
            return True

        required_fields = self._config.input_schema.get("required", [])
        for field_name in required_fields:
            if field_name not in input_data:
                self.logger.warning(
                    "validation_failed",
                    reason=f"Missing required field: {field_name}"
                )
                return False

        return True

    async def health_check(self) -> bool:
        """Check if the CLI adapter is healthy."""
        try:
            result = await self.execute({"test": True})
            return result.status == ExecutionStatus.SUCCESS
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup running process if any."""
        await self._terminate_process()

    async def _terminate_process(self) -> None:
        """Terminate running process."""
        if self._process and self._process.returncode is None:
            try:
                if os.name == 'nt':
                    self._process.terminate()
                else:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    else:
                        self._process.kill()
            except ProcessLookupError:
                pass

    def _build_command(self, input_data: Dict[str, Any]) -> str:
        """Build command with arguments from input data."""
        command = self._config.command
        
        args = input_data.get("args", [])
        if isinstance(args, list):
            arg_str = " ".join(str(arg) for arg in args)
            command = f"{command} {arg_str}"
        elif isinstance(args, str):
            command = f"{command} {args}"
        
        for key, value in input_data.items():
            if key not in ["args", "env"]:
                if isinstance(value, bool):
                    if value:
                        command = f"{command} --{key}"
                elif isinstance(value, (str, int, float)):
                    command = f"{command} --{key} {value}"
                elif isinstance(value, list):
                    for item in value:
                        command = f"{command} --{key} {item}"

        return command

    def _build_environment(self) -> Dict[str, str]:
        """Build environment variables."""
        env = dict(os.environ)
        env.update(self._config.env_vars)
        return env
