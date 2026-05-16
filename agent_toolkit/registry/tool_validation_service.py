"""Tool validation service for validating tool configurations, schemas, and inputs."""

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json
import re
from dataclasses import dataclass

from agent_toolkit.shared.custom_exceptions import ValidationError
# from agent_toolkit.shared.structured_logging import LoggerMixin
from agent_toolkit.registry.registry_models import AdapterType
from agent_toolkit.registry.registry_schemas import ToolCreate


class ValidationSeverity(str, Enum):
    """Validation severity level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    field: str
    message: str
    severity: ValidationSeverity
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of tool validation."""
    valid: bool
    issues: List[ValidationIssue]
    warnings: List[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class ToolValidationService:
    """Service for validating tools and their configurations."""

    # Common JSON Schema keywords
    JSON_SCHEMA_KEYWORDS = {
        "type", "properties", "items", "required", "additionalProperties",
        "pattern", "minimum", "maximum", "minLength", "maxLength", "enum",
        "default", "description", "format", "oneOf", "anyOf", "allOf"
    }

    # Reserved tool names
    RESERVED_NAMES = {
        "tool", "tools", "registry", "system", "admin", "test",
        "null", "true", "false", "none", "undefined"
    }

    # Semantic version pattern
    SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")

    # Valid adapter configurations
    VALID_ADAPTER_CONFIGS = {
        AdapterType.HTTP: {"url", "method", "headers", "timeout", "auth_type"},
        AdapterType.CLI: {"command", "args", "env", "timeout", "cwd"},
        AdapterType.SDK: {"package", "module", "class_name", "method_name", "import_path"},
        AdapterType.FUNCTION: {"module", "function_name", "import_path"},
        AdapterType.GRAPHQL: {"url", "query", "variables", "headers", "timeout"},
        AdapterType.WEBSOCKET: {"url", "message_format", "timeout", "headers"}
    }

    def __init__(self):
        pass

    async def validate_tool(self, tool_data: ToolCreate) -> ValidationResult:
        """
        Validate a complete tool configuration.
        
        Args:
            tool_data: The tool data to validate
            
        Returns:
            ValidationResult with validation status and issues
        """
        issues: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        # Validate basic fields
        await self._validate_name(tool_data.name, issues, warnings)
        await self._validate_version(tool_data.version, issues, warnings)
        await self._validate_description(tool_data.description, issues, warnings)
        await self._validate_author(tool_data.author, issues, warnings)

        # Validate schemas
        await self._validate_json_schema(tool_data.input_schema, "input_schema", issues, warnings)
        if tool_data.output_schema:
            await self._validate_json_schema(tool_data.output_schema, "output_schema", issues, warnings)

        # Validate adapter configuration
        await self._validate_adapter_config(
            tool_data.adapter_type,
            tool_data.adapter_config,
            issues,
            warnings
        )

        # Validate tags
        await self._validate_tags(tool_data.tags, issues, warnings)

        # Validate metadata
        if tool_data.extra_metadata:
            await self._validate_metadata(tool_data.extra_metadata, issues, warnings)

        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)

        # 暂时注释掉 logger 调用，避免问题
        # self.logger.info(
        #     "tool_validation_completed",
        #     tool_name=tool_data.name,
        #     valid=is_valid,
        #     error_count=sum(1 for i in issues if i.severity == ValidationSeverity.ERROR),
        #     warning_count=len(warnings)
        # )

        return ValidationResult(
            valid=is_valid,
            issues=issues,
            warnings=warnings
        )

    async def _validate_name(self, name: str, issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate tool name."""
        if len(name) < 2:
            issues.append(ValidationIssue(
                field="name",
                message="Tool name must be at least 2 characters long",
                severity=ValidationSeverity.ERROR
            ))
        elif len(name) > 200:
            issues.append(ValidationIssue(
                field="name",
                message="Tool name must be no more than 200 characters long",
                severity=ValidationSeverity.ERROR
            ))

        if name.lower() in self.RESERVED_NAMES:
            issues.append(ValidationIssue(
                field="name",
                message=f"'{name}' is a reserved name",
                severity=ValidationSeverity.ERROR,
                suggestion="Choose a different name"
            ))

        if not re.match(r"^[a-z0-9_-]+$", name):
            issues.append(ValidationIssue(
                field="name",
                message="Tool name may only contain lowercase letters, numbers, underscores, and hyphens",
                severity=ValidationSeverity.ERROR
            ))

        if name.startswith("-") or name.endswith("-"):
            issues.append(ValidationIssue(
                field="name",
                message="Tool name cannot start or end with a hyphen",
                severity=ValidationSeverity.ERROR
            ))

    async def _validate_version(self, version: str, issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate semantic version."""
        if not self.SEMVER_PATTERN.match(version):
            issues.append(ValidationIssue(
                field="version",
                message="Version must follow semantic versioning format (e.g., 1.0.0, 1.0.0-beta, 1.0.0+build)",
                severity=ValidationSeverity.ERROR,
                suggestion="Use format: major.minor.patch[-prerelease][+build]"
            ))

        major, minor, patch = version.split(".")[:3]
        if major.startswith("0") and len(major) > 1:
            warnings.append(ValidationIssue(
                field="version",
                message="Major version should not have leading zeros",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Use {int(major)}.{minor}.{patch}"
            ))

    async def _validate_description(self, description: str, issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate tool description."""
        if len(description.strip()) < 10:
            issues.append(ValidationIssue(
                field="description",
                message="Description should be at least 10 characters long",
                severity=ValidationSeverity.ERROR,
                suggestion="Provide a more detailed description of what this tool does"
            ))

        if len(description) > 5000:
            warnings.append(ValidationIssue(
                field="description",
                message="Description is very long (>5000 characters)",
                severity=ValidationSeverity.WARNING
            ))

    async def _validate_author(self, author: str, issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate author information."""
        if len(author.strip()) < 2:
            issues.append(ValidationIssue(
                field="author",
                message="Author name must be at least 2 characters",
                severity=ValidationSeverity.ERROR
            ))

    async def _validate_json_schema(
        self,
        schema: Dict[str, Any],
        field_name: str,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue]
    ) -> None:
        """Validate JSON Schema."""
        if not isinstance(schema, dict):
            issues.append(ValidationIssue(
                field=field_name,
                message="Schema must be an object",
                severity=ValidationSeverity.ERROR
            ))
            return

        # Check that it has a type or uses composition keywords
        has_type = "type" in schema
        has_composition = any(key in schema for key in ["oneOf", "anyOf", "allOf"])
        if not has_type and not has_composition:
            issues.append(ValidationIssue(
                field=field_name,
                message="Schema must specify a 'type' or use composition keywords (oneOf, anyOf, allOf)",
                severity=ValidationSeverity.ERROR
            ))

        # Validate required fields
        if "required" in schema:
            if not isinstance(schema["required"], list):
                issues.append(ValidationIssue(
                    field=f"{field_name}.required",
                    message="'required' must be an array",
                    severity=ValidationSeverity.ERROR
                ))
            elif "properties" in schema:
                for required_field in schema["required"]:
                    if required_field not in schema["properties"]:
                        issues.append(ValidationIssue(
                            field=f"{field_name}.required",
                            message=f"Required field '{required_field}' not defined in properties",
                            severity=ValidationSeverity.ERROR
                        ))

        # Validate properties if present
        if "properties" in schema:
            if not isinstance(schema["properties"], dict):
                issues.append(ValidationIssue(
                    field=f"{field_name}.properties",
                    message="'properties' must be an object",
                    severity=ValidationSeverity.ERROR
                ))
            else:
                for prop_name, prop_schema in schema["properties"].items():
                    await self._validate_json_schema(
                        prop_schema,
                        f"{field_name}.properties.{prop_name}",
                        issues,
                        warnings
                    )

        # Validate items if present (for arrays)
        if "items" in schema:
            if isinstance(schema["items"], dict):
                await self._validate_json_schema(
                    schema["items"],
                    f"{field_name}.items",
                    issues,
                    warnings
                )
            elif isinstance(schema["items"], list):
                for idx, item_schema in enumerate(schema["items"]):
                    await self._validate_json_schema(
                        item_schema,
                        f"{field_name}.items[{idx}]",
                        issues,
                        warnings
                    )

    async def _validate_adapter_config(
        self,
        adapter_type: str,
        adapter_config: Dict[str, Any],
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue]
    ) -> None:
        """Validate adapter configuration."""
        if adapter_type not in self.VALID_ADAPTER_CONFIGS:
            issues.append(ValidationIssue(
                field="adapter_type",
                message=f"Invalid adapter type: {adapter_type}",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Use one of: {', '.join(self.VALID_ADAPTER_CONFIGS.keys())}"
            ))
            return

        valid_keys = self.VALID_ADAPTER_CONFIGS[adapter_type]
        provided_keys = set(adapter_config.keys())

        # Check for unknown keys
        unknown_keys = provided_keys - valid_keys
        if unknown_keys:
            warnings.append(ValidationIssue(
                field="adapter_config",
                message=f"Unknown configuration keys: {', '.join(unknown_keys)}",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Valid keys: {', '.join(valid_keys)}"
            ))

        # Check required fields for specific adapter types
        if adapter_type == AdapterType.HTTP:
            if "url" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config.url",
                    message="URL is required for HTTP adapter",
                    severity=ValidationSeverity.ERROR
                ))
            elif not self._is_valid_url(adapter_config["url"]):
                issues.append(ValidationIssue(
                    field="adapter_config.url",
                    message="Invalid URL format",
                    severity=ValidationSeverity.ERROR
                ))

        elif adapter_type == AdapterType.CLI:
            if "command" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config.command",
                    message="Command is required for CLI adapter",
                    severity=ValidationSeverity.ERROR
                ))

        elif adapter_type == AdapterType.SDK:
            if "package" not in adapter_config and "module" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config",
                    message="Either 'package' or 'module' is required for SDK adapter",
                    severity=ValidationSeverity.ERROR
                ))

        elif adapter_type == AdapterType.FUNCTION:
            if "module" not in adapter_config or "function_name" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config",
                    message="'module' and 'function_name' are required for Function adapter",
                    severity=ValidationSeverity.ERROR
                ))

        elif adapter_type == AdapterType.GRAPHQL:
            if "url" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config.url",
                    message="URL is required for GraphQL adapter",
                    severity=ValidationSeverity.ERROR
                ))
            if "query" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config.query",
                    message="Query is required for GraphQL adapter",
                    severity=ValidationSeverity.ERROR
                ))

        elif adapter_type == AdapterType.WEBSOCKET:
            if "url" not in adapter_config:
                issues.append(ValidationIssue(
                    field="adapter_config.url",
                    message="URL is required for WebSocket adapter",
                    severity=ValidationSeverity.ERROR
                ))

    async def _validate_tags(self, tags: List[str], issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate tags."""
        if len(tags) > 50:
            warnings.append(ValidationIssue(
                field="tags",
                message="Too many tags (maximum 50 recommended)",
                severity=ValidationSeverity.WARNING
            ))

        seen_tags = set()
        for tag in tags:
            if not tag.strip():
                issues.append(ValidationIssue(
                    field="tags",
                    message="Empty tags are not allowed",
                    severity=ValidationSeverity.ERROR
                ))
            elif len(tag) > 50:
                warnings.append(ValidationIssue(
                    field="tags",
                    message=f"Tag '{tag[:20]}...' is too long (maximum 50 characters)",
                    severity=ValidationSeverity.WARNING
                ))
            elif tag in seen_tags:
                warnings.append(ValidationIssue(
                    field="tags",
                    message=f"Duplicate tag: '{tag}'",
                    severity=ValidationSeverity.WARNING
                ))
            seen_tags.add(tag)

    async def _validate_metadata(self, metadata: Dict[str, Any], issues: List[ValidationIssue], warnings: List[ValidationIssue]) -> None:
        """Validate metadata."""
        try:
            json.dumps(metadata)
        except (TypeError, ValueError):
            issues.append(ValidationIssue(
                field="metadata",
                message="Metadata must be JSON-serializable",
                severity=ValidationSeverity.ERROR
            ))

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme in ["http", "https", "ws", "wss"], result.netloc])
        except Exception:
            return False

    async def validate_input_data(self, input_data: Dict[str, Any], input_schema: Dict[str, Any]) -> ValidationResult:
        """
        Validate input data against the input schema.
        
        Args:
            input_data: The input data to validate
            input_schema: The schema to validate against
            
        Returns:
            ValidationResult with validation status and issues
        """
        issues: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        try:
            import jsonschema
            jsonschema.validate(instance=input_data, schema=input_schema)
        except ImportError:
            # Fall back to basic validation if jsonschema is not available
            warnings.append(ValidationIssue(
                field="input_data",
                message="jsonschema library not available, performing basic validation only",
                severity=ValidationSeverity.WARNING
            ))
            await self._basic_data_validation(input_data, input_schema, "input_data", issues, warnings)
        except jsonschema.ValidationError as e:
            issues.append(ValidationIssue(
                field=".".join(str(p) for p in e.path) if e.path else "input_data",
                message=e.message,
                severity=ValidationSeverity.ERROR
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                field="input_data",
                message=f"Validation error: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        is_valid = len(issues) == 0
        return ValidationResult(valid=is_valid, issues=issues, warnings=warnings)

    async def _basic_data_validation(
        self,
        data: Any,
        schema: Dict[str, Any],
        field_name: str,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue]
    ) -> None:
        """Basic data validation when jsonschema is not available."""
        expected_type = schema.get("type")
        if expected_type:
            type_mapping = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
                "null": type(None)
            }
            
            expected_python_type = type_mapping.get(expected_type)
            if expected_python_type and not isinstance(data, expected_python_type):
                issues.append(ValidationIssue(
                    field=field_name,
                    message=f"Expected type {expected_type}, got {type(data).__name__}",
                    severity=ValidationSeverity.ERROR
                ))
                return

        if expected_type == "object" and isinstance(data, dict):
            required = schema.get("required", [])
            for req_field in required:
                if req_field not in data:
                    issues.append(ValidationIssue(
                        field=f"{field_name}.{req_field}",
                        message=f"Required field '{req_field}' is missing",
                        severity=ValidationSeverity.ERROR
                    ))

            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    await self._basic_data_validation(
                        data[prop_name],
                        prop_schema,
                        f"{field_name}.{prop_name}",
                        issues,
                        warnings
                    )

        elif expected_type == "array" and isinstance(data, list):
            items_schema = schema.get("items", {})
            for idx, item in enumerate(data):
                await self._basic_data_validation(
                    item,
                    items_schema,
                    f"{field_name}[{idx}]",
                    issues,
                    warnings
                )
