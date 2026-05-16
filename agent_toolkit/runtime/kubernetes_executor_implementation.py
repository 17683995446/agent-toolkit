"""Kubernetes executor implementation for tool runtime."""

import asyncio
import json
from typing import Any, Optional, Dict
from dataclasses import dataclass

from agent_toolkit.runtime.base_executor import (
    BaseExecutor,
    ExecutorConfig,
    ExecutionResult,
    ExecutionStatus,
)
from agent_toolkit.shared.structured_logging import LoggerMixin


@dataclass
class KubernetesExecutorConfig(ExecutorConfig):
    """Configuration for Kubernetes executor."""
    namespace: str = "default"
    image: str = "python:3.12-slim"
    service_account: Optional[str] = None
    node_selector: Optional[Dict[str, str]] = None
    pod_template: Optional[Dict[str, Any]] = None


class KubernetesExecutor(BaseExecutor, LoggerMixin):
    """Executor that runs tools in Kubernetes pods."""

    def __init__(self, config: KubernetesExecutorConfig):
        super().__init__(config)
        self._config = config
        self._core_api = None
        self._batch_api = None

    async def initialize(self) -> None:
        """Initialize Kubernetes client."""
        if self._is_initialized:
            return

        try:
            from kubernetes import client, config

            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

            self._core_api = client.CoreV1Api()
            self._batch_api = client.BatchV1Api()

            await super().initialize()

            self.logger.info(
                "kubernetes_executor_initialized",
                namespace=self._config.namespace
            )
        except ImportError:
            self.logger.warning("kubernetes_client_not_installed")
            raise
        except Exception as e:
            self.logger.error("kubernetes_init_failed", error=str(e))
            raise

    async def _do_execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute tool in Kubernetes pod."""
        if not self._core_api:
            raise RuntimeError("Kubernetes client not initialized")

        pod_name = f"tool-exec-{tool_id[:8]}-{uuid.uuid4().hex[:8]}"

        try:
            await self._create_pod(pod_name, tool_id, input_data, context)
            
            result = await self._wait_for_pod(pod_name)

            return result

        except Exception as e:
            self.logger.error("kubernetes_execution_failed", error=str(e))
            raise

        finally:
            await self._cleanup_pod(pod_name)

    async def _create_pod(
        self,
        pod_name: str,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Create a Kubernetes pod for execution."""
        from kubernetes import client

        env = [
            client.V1EnvVar(name="TOOL_ID", value=tool_id),
            client.V1EnvVar(
                name="TOOL_INPUT",
                value=json.dumps(input_data)
            ),
        ]

        if context:
            env.append(
                client.V1EnvVar(
                    name="EXECUTION_CONTEXT",
                    value=json.dumps(context)
                )
            )

        for key, value in self._config.environment.items():
            env.append(client.V1EnvVar(name=key, value=value))

        resources = client.V1ResourceRequirements(
            limits={
                "memory": self._config.memory_limit,
                "cpu": self._config.cpu_limit,
            },
            requests={
                "memory": self._config.memory_limit,
                "cpu": self._config.cpu_limit,
            }
        )

        pod_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": self._config.namespace,
                "labels": {
                    "app": "agent-toolkit",
                    "tool-id": tool_id,
                }
            },
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "name": "tool-executor",
                        "image": self._config.image,
                        "command": ["python", "-c", f"print('Executing tool {tool_id}')"],
                        "env": env,
                        "resources": resources,
                    }
                ],
                "activeDeadlineSeconds": self._config.timeout,
            }
        }

        if self._config.service_account:
            pod_spec["spec"]["serviceAccountName"] = self._config.service_account

        if self._config.node_selector:
            pod_spec["spec"]["nodeSelector"] = self._config.node_selector

        await asyncio.to_thread(
            self._core_api.create_namespaced_pod,
            namespace=self._config.namespace,
            body=pod_spec,
        )

        self.logger.info(
            "kubernetes_pod_created",
            pod_name=pod_name,
            namespace=self._config.namespace
        )

    async def _wait_for_pod(self, pod_name: str) -> ExecutionResult:
        """Wait for pod to complete and get result."""
        from kubernetes import client

        while True:
            await asyncio.sleep(1)

            pod = await asyncio.to_thread(
                self._core_api.read_namespaced_pod,
                name=pod_name,
                namespace=self._config.namespace,
            )

            phase = pod.status.phase

            if phase == "Succeeded":
                logs = await self._get_pod_logs(pod_name)
                return ExecutionResult(
                    execution_id=pod_name,
                    tool_id=pod.metadata.labels.get("tool-id", ""),
                    status=ExecutionStatus.SUCCESS,
                    output={"logs": logs},
                    exit_code=0,
                    metadata={"pod_name": pod_name, "namespace": self._config.namespace}
                )

            elif phase == "Failed":
                logs = await self._get_pod_logs(pod_name)
                return ExecutionResult(
                    execution_id=pod_name,
                    tool_id=pod.metadata.labels.get("tool-id", ""),
                    status=ExecutionStatus.FAILED,
                    output={"logs": logs},
                    exit_code=1,
                    metadata={"pod_name": pod_name, "namespace": self._config.namespace}
                )

            elif phase == "Running":
                continue

            else:
                await asyncio.sleep(1)

    async def _get_pod_logs(self, pod_name: str) -> str:
        """Get logs from pod."""
        try:
            logs = await asyncio.to_thread(
                self._core_api.read_namespaced_pod_log,
                name=pod_name,
                namespace=self._config.namespace,
            )
            return logs
        except Exception as e:
            self.logger.warning("failed_to_get_pod_logs", error=str(e))
            return ""

    async def _cleanup_pod(self, pod_name: str) -> None:
        """Cleanup pod after execution."""
        try:
            await asyncio.to_thread(
                self._core_api.delete_namespaced_pod,
                name=pod_name,
                namespace=self._config.namespace,
                body=client.V1DeleteOptions(),
            )
            self.logger.debug("pod_cleaned_up", pod_name=pod_name)
        except Exception as e:
            self.logger.warning("pod_cleanup_failed", error=str(e))

    async def health_check(self) -> bool:
        """Check Kubernetes cluster health."""
        if not self._core_api:
            return False
        try:
            await asyncio.to_thread(self._core_api.get_api_resources)
            return True
        except Exception:
            return False

    async def list_pods(self, label_selector: str = "app=agent-toolkit") -> list[Dict[str, Any]]:
        """List pods in namespace."""
        if not self._core_api:
            return []

        pods = await asyncio.to_thread(
            self._core_api.list_namespaced_pod,
            namespace=self._config.namespace,
            label_selector=label_selector,
        )

        return [
            {
                "name": p.metadata.name,
                "status": p.status.phase,
                "created": p.metadata.creation_timestamp.isoformat(),
            }
            for p in pods.items
        ]
