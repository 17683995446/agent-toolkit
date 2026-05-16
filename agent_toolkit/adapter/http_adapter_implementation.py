"""HTTP Adapter implementation."""

import time
import hashlib
from typing import Any, Optional, Dict
from urllib.parse import urljoin, urlencode

import httpx
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
from agent_toolkit.shared.application_settings import get_settings


class HTTPAdapterConfig(BaseModel):
    """Configuration for HTTP adapter."""
    base_url: str = Field(..., description="Base URL for the API")
    endpoint: str = Field("/", description="API endpoint path")
    method: str = Field("GET", description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    query_params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    body_schema: Optional[Dict[str, Any]] = Field(None, description="Request body JSON schema")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Response JSON schema")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")
    auth_type: Optional[str] = Field(None, description="Authentication type (basic, bearer, api_key)")
    auth_credentials: Optional[Dict[str, str]] = Field(None, description="Authentication credentials")
    cache_responses: bool = Field(False, description="Enable response caching")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input JSON schema")


class HTTPAdapter(BaseAdapter, LoggerMixin):
    """Adapter for HTTP/REST APIs."""

    def __init__(
        self,
        config: HTTPAdapterConfig,
        metadata: Optional[ToolMetadata] = None,
    ):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, tuple[Any, float]] = {}
        super().__init__(config=config, metadata=metadata)

    @property
    def adapter_type(self) -> AdapterType:
        """Get adapter type."""
        return AdapterType.HTTP

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        settings = get_settings()
        
        headers = {
            "User-Agent": "AgentToolkit-HTTPAdapter/0.1.0",
            **self._config.headers
        }
        
        if self._config.auth_type == "bearer" and self._config.auth_credentials:
            token = self._config.auth_credentials.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        elif self._config.auth_type == "api_key" and self._config.auth_credentials:
            api_key = self._config.auth_credentials.get("api_key", "")
            header_name = self._config.auth_credentials.get("header_name", "X-API-Key")
            headers[header_name] = api_key

        timeout = httpx.Timeout(
            connect=10.0,
            read=float(self._config.timeout),
            write=10.0,
            pool=5.0
        )

        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=headers,
            timeout=timeout,
            verify=self._config.verify_ssl,
            follow_redirects=self._config.follow_redirects,
        )

        self.logger.info(
            "http_adapter_initialized",
            base_url=self._config.base_url,
            endpoint=self._config.endpoint
        )

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute HTTP request."""
        start_time = time.time()

        if not self._client:
            await self.initialize()

        cache_key = self._generate_cache_key(input_data)
        if self._config.cache_responses and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl:
                self.logger.debug("cache_hit", cache_key=cache_key)
                return AdapterResult(
                    status=ExecutionStatus.SUCCESS,
                    data=cached_data,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    metadata={"cached": True}
                )

        try:
            url = self._build_url(input_data)
            method = self._config.method.upper()
            headers = self._build_headers(input_data)
            params = self._build_query_params(input_data)
            body = self._build_body(input_data)

            self.logger.debug(
                "http_request_start",
                method=method,
                url=url,
            )

            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body if body else None,
            )

            execution_time = (time.time() - start_time) * 1000

            if response.status_code < 400:
                response_data = self._parse_response(response)
                
                if self._config.cache_responses:
                    self._cache[cache_key] = (response_data, time.time())
                
                self.logger.info(
                    "http_request_success",
                    status_code=response.status_code,
                    execution_time_ms=execution_time
                )

                return AdapterResult(
                    status=ExecutionStatus.SUCCESS,
                    data=response_data,
                    execution_time_ms=execution_time,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    }
                )
            else:
                self.logger.warning(
                    "http_request_error",
                    status_code=response.status_code,
                    response_body=response.text[:500]
                )

                return AdapterResult(
                    status=ExecutionStatus.FAILURE,
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                    execution_time_ms=execution_time,
                    metadata={"status_code": response.status_code}
                )

        except httpx.TimeoutException as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error("http_timeout", error=str(e))
            return AdapterResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"Request timeout after {self._config.timeout}s",
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error("http_error", error=str(e))
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        if not self._config.input_schema:
            return True

        required_fields = self._config.input_schema.get("required", [])
        for field in required_fields:
            if field not in input_data:
                self.logger.warning(
                    "validation_failed",
                    reason=f"Missing required field: {field}"
                )
                return False

        return True

    async def health_check(self) -> bool:
        """Check if the HTTP endpoint is reachable."""
        if not self._client:
            return False

        try:
            response = await self._client.get("/", timeout=5.0)
            return response.status_code < 500
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._cache.clear()

    def _build_url(self, input_data: Dict[str, Any]) -> str:
        """Build request URL."""
        endpoint = self._config.endpoint
        
        path_params = input_data.pop("path_params", {})
        for key, value in path_params.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))
        
        return endpoint

    def _build_headers(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers."""
        headers = {}
        
        custom_headers = input_data.pop("headers", {})
        headers.update(custom_headers)
        
        return headers

    def _build_query_params(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters."""
        params = dict(self._config.query_params)
        
        query_params = input_data.pop("query_params", {})
        params.update(query_params)
        
        return params

    def _build_body(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build request body."""
        body = input_data.pop("body", {})
        body.update(input_data)
        
        return body if body else None

    def _parse_response(self, response: httpx.Response) -> Any:
        """Parse HTTP response."""
        content_type = response.headers.get("content-type", "")
        
        if "application/json" in content_type:
            return response.json()
        elif "text/" in content_type:
            return {"text": response.text}
        else:
            return {"content": response.content}

    def _generate_cache_key(self, input_data: Dict[str, Any]) -> str:
        """Generate cache key for input data."""
        data_str = str(sorted(input_data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()
