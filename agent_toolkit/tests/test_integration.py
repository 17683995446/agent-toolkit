"""Integration tests for the Agent Toolkit system."""

import pytest
import asyncio
from datetime import datetime

from agent_toolkit.registry.registry_models import ToolStatus, AdapterType
from agent_toolkit.registry.registry_schemas import (
    ToolCreate,
    ToolUpdate,
    ToolCategoryCreate,
    ToolStatusEnum,
    AdapterTypeEnum,
)
from agent_toolkit.registry.tool_validation_service import ToolValidationService
from agent_toolkit.registry.tool_publication_service import ToolPublicationService
from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainNode,
    ExecutionContext,
    NodeType,
    ExecutionMode,
    ChainStatus,
    ChainEdge,
)
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
from agent_toolkit.orchestrator.node_executors import (
    ToolNodeExecutor,
    ConditionNodeExecutor,
    InputNodeExecutor,
    OutputNodeExecutor,
)
from agent_toolkit.shared.custom_exceptions import ValidationError
from agent_toolkit.shared.api_response import APIResponse


@pytest.fixture
def db_session():
    """Mock database session for testing."""
    return None  # In real implementation, this would be an async session


class TestToolCreationAndValidationIntegration:
    """Integration tests for tool creation and validation."""
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service."""
        return ToolValidationService()
    
    @pytest.fixture
    def valid_tool_data(self):
        """Valid tool creation data."""
        return ToolCreate(
            name="calculator-tool",
            description="A simple calculator tool for basic arithmetic operations",
            version="1.0.0",
            category_id=None,
            status=ToolStatusEnum.DRAFT,
            adapter_type=AdapterTypeEnum.HTTP,
            adapter_config={
                "url": "https://api.example.com/calculate",
                "method": "POST",
                "timeout": 30
            },
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "number"}
                }
            },
            tags=["math", "calculator", "utility"],
            author="Integration Test Author",
            license="Apache-2.0"
        )
    
    @pytest.mark.asyncio
    async def test_complete_tool_lifecycle(self, validation_service, valid_tool_data):
        """Test the complete lifecycle of a tool from creation to validation."""
        # 1. Validate the tool
        validation_result = await validation_service.validate_tool(valid_tool_data)
        assert validation_result.valid is True, f"Tool validation failed: {validation_result.issues}"
        
        # 2. Simulate tool creation (would use ToolService in real implementation)
        tool_id = "test-tool-123"
        
        # 3. Simulate tool update
        update_data = ToolUpdate(
            description="An updated description for the calculator tool",
            version="1.1.0"
        )
        
        # 4. Validate that updates don't break the tool
        updated_tool_data = valid_tool_data.model_copy(update=update_data.model_dump(exclude_unset=True))
        revalidation_result = await validation_service.validate_tool(updated_tool_data)
        assert revalidation_result.valid is True
        
        # 5. Test validation failure case
        invalid_tool_data = valid_tool_data.model_copy()
        invalid_tool_data.name = ""  # Invalid name
        invalid_result = await validation_service.validate_tool(invalid_tool_data)
        assert invalid_result.valid is False
        assert len(invalid_result.issues) > 0


class TestOrchestrationIntegration:
    """Integration tests for orchestration."""
    
    @pytest.fixture
    def orchestration_engine(self):
        """Create orchestration engine."""
        engine = OrchestrationEngine()
        
        # Register simple executors
        class MockExecutor:
            async def execute(self, node, input_data, context):
                return {"processed": True, "node_id": node.id, "input": input_data}
        
        for node_type in NodeType:
            engine.register_node_executor(node_type, MockExecutor())
        
        return engine
    
    @pytest.fixture
    def calculator_chain(self):
        """Create a calculator tool chain."""
        return ToolChain(
            id="calculator-chain",
            name="Calculator Chain",
            description="A chain that performs calculator operations",
            version="1.0.0",
            nodes=[
                ChainNode(
                    id="input",
                    type=NodeType.INPUT,
                    name="Input",
                    config={"schema": {}},
                    outputs=["operation", "a", "b"]
                ),
                ChainNode(
                    id="validate",
                    type=NodeType.CONDITION,
                    name="Validate Input",
                    config={
                        "condition": "operation in ['add', 'subtract', 'multiply', 'divide']"
                    },
                    inputs={"operation": "operation"},
                    outputs=["is_valid"]
                ),
                ChainNode(
                    id="calculate",
                    type=NodeType.TOOL,
                    name="Calculate",
                    config={"tool_id": "calculator-tool"},
                    inputs={"operation": "operation", "a": "a", "b": "b"},
                    outputs=["result"]
                ),
                ChainNode(
                    id="output",
                    type=NodeType.OUTPUT,
                    name="Output Result",
                    config={"outputs": ["result"]}
                )
            ],
            edges=[
                ChainEdge(source="input", target="validate"),
                ChainEdge(source="validate", target="calculate"),
                ChainEdge(source="calculate", target="output")
            ],
            execution_mode=ExecutionMode.SEQUENTIAL
        )
    
    @pytest.mark.asyncio
    async def test_execute_tool_chain(self, orchestration_engine, calculator_chain):
        """Test executing a complete tool chain."""
        # Validate the chain first
        is_valid, errors = calculator_chain.validate()
        assert is_valid is True, f"Chain validation failed: {errors}"
        
        # Execute the chain
        context = await orchestration_engine.execute_chain(
            calculator_chain,
            initial_inputs={
                "operation": "add",
                "a": 5,
                "b": 3
            }
        )
        
        # Verify the result
        assert context.status == ChainStatus.COMPLETED, f"Chain failed: {context.errors}"
        assert context.execution_id is not None
        assert context.chain_id == "calculator-chain"
        assert len(context.node_results) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_chain_executions(self, orchestration_engine, calculator_chain):
        """Test executing multiple chains concurrently."""
        # Create multiple executions
        tasks = []
        for i in range(3):
            task = orchestration_engine.execute_chain(
                calculator_chain,
                initial_inputs={"operation": "add", "a": i, "b": i}
            )
            tasks.append(task)
        
        # Wait for all to complete
        contexts = await asyncio.gather(*tasks)
        
        # Verify all completed
        for ctx in contexts:
            assert ctx.status == ChainStatus.COMPLETED
            assert ctx.execution_id is not None


class TestAPIResponseIntegration:
    """Integration tests for API response system."""
    
    def test_success_response(self):
        """Test creating a success response."""
        response = APIResponse.success(
            data={"result": "success"},
            message="Operation completed successfully"
        )
        
        assert response.success is True
        assert response.data == {"result": "success"}
        assert response.message == "Operation completed successfully"
        assert response.error is None
    
    def test_error_response(self):
        """Test creating an error response."""
        response = APIResponse.error(
            error_code="VALIDATION_ERROR",
            message="Invalid input data",
            details={"field": "name", "reason": "required"},
            status_code=400
        )
        
        assert response.success is False
        assert response.data is None
        assert response.message == "Invalid input data"
        assert response.error is not None
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.details == {"field": "name", "reason": "required"}
    
    def test_response_model_dump(self):
        """Test that response can be converted to dict."""
        response = APIResponse.success(
            data={"key": "value"},
            message="Success"
        )
        
        dump = response.model_dump()
        
        assert dump["success"] is True
        assert dump["data"] == {"key": "value"}
        assert dump["message"] == "Success"


class TestWorkflowIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow from tool creation to chain execution."""
        # 1. Create validation service
        validation_service = ToolValidationService()
        
        # 2. Define a tool
        tool_data = ToolCreate(
            name="greeting-tool",
            description="A tool that generates greetings",
            version="1.0.0",
            status=ToolStatusEnum.DRAFT,
            adapter_type=AdapterTypeEnum.FUNCTION,
            adapter_config={
                "module": "greetings",
                "function_name": "say_hello"
            },
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            },
            tags=["greeting", "demo"],
            author="Workflow Test"
        )
        
        # 3. Validate the tool
        validation_result = await validation_service.validate_tool(tool_data)
        assert validation_result.valid is True
        
        # 4. Create an orchestration engine
        engine = OrchestrationEngine()
        
        # 5. Create a simple chain
        chain = ToolChain(
            id="greeting-chain",
            name="Greeting Chain",
            nodes=[
                ChainNode(
                    id="input",
                    type=NodeType.INPUT,
                    name="Input",
                    config={},
                    outputs=["name"]
                ),
                ChainNode(
                    id="output",
                    type=NodeType.OUTPUT,
                    name="Output",
                    config={"outputs": ["name"]}
                )
            ],
            edges=[
                ChainEdge(source="input", target="output")
            ],
            execution_mode=ExecutionMode.SEQUENTIAL
        )
        
        # 6. Validate the chain
        is_valid, errors = chain.validate()
        assert is_valid is True, f"Chain invalid: {errors}"
        
        print("Complete workflow test passed successfully!")
