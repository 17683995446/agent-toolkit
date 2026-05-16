"""Tests for orchestration engine."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainNode,
    ExecutionContext,
    NodeExecutionResult,
    NodeType,
    ExecutionMode,
    ChainStatus,
    RetryPolicy,
    ChainEdge,
)
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine


@pytest.fixture
def simple_tool_chain():
    """Create a simple tool chain for testing."""
    return ToolChain(
        id="test-chain",
        name="Test Chain",
        description="A simple test chain",
        version="1.0.0",
        nodes=[
            ChainNode(
                id="input",
                type=NodeType.INPUT,
                name="Input Node",
                config={"schema": {}},
                outputs=["input_data"]
            ),
            ChainNode(
                id="process",
                type=NodeType.TOOL,
                name="Process Node",
                config={"tool_id": "test-tool"},
                inputs={"input": "input_data"},
                outputs=["result"]
            ),
            ChainNode(
                id="output",
                type=NodeType.OUTPUT,
                name="Output Node",
                config={"outputs": ["result"]}
            )
        ],
        edges=[
            ChainEdge(source="input", target="process"),
            ChainEdge(source="process", target="output")
        ],
        execution_mode=ExecutionMode.SEQUENTIAL
    )


@pytest.fixture
def orchestration_engine():
    """Create an orchestration engine instance."""
    engine = OrchestrationEngine()
    
    # Register mock executors
    for node_type in NodeType:
        mock_executor = MagicMock()
        mock_executor.execute = AsyncMock(return_value={"result": "success"})
        engine.register_node_executor(node_type, mock_executor)
    
    return engine


class TestToolChainValidation:
    """Tests for ToolChain validation."""
    
    def test_validate_empty_chain(self):
        """A chain with no nodes should be invalid."""
        chain = ToolChain(
            id="empty-chain",
            name="Empty Chain",
            nodes=[],
            edges=[]
        )
        
        is_valid, errors = chain.validate()
        
        assert is_valid is False
        assert "Chain must have at least one node" in errors
    
    def test_validate_chain_with_valid_nodes(self, simple_tool_chain):
        """A chain with valid nodes should be valid."""
        is_valid, errors = simple_tool_chain.validate()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_chain_with_unknown_edge_source(self, simple_tool_chain):
        """A chain with edge referencing unknown node should be invalid."""
        simple_tool_chain.edges.append(
            ChainEdge(source="unknown-node", target="output")
        )
        
        is_valid, errors = simple_tool_chain.validate()
        
        assert is_valid is False
        assert any("Edge references unknown source node" in e for e in errors)
    
    def test_validate_chain_with_unknown_edge_target(self, simple_tool_chain):
        """A chain with edge referencing unknown target should be invalid."""
        simple_tool_chain.edges.append(
            ChainEdge(source="input", target="unknown-node")
        )
        
        is_valid, errors = simple_tool_chain.validate()
        
        assert is_valid is False
        assert any("Edge references unknown target node" in e for e in errors)
    
    def test_get_node(self, simple_tool_chain):
        """Should be able to get a node by ID."""
        node = simple_tool_chain.get_node("input")
        
        assert node is not None
        assert node.id == "input"
        assert node.type == NodeType.INPUT
    
    def test_get_node_not_found(self, simple_tool_chain):
        """Getting a non-existent node should return None."""
        node = simple_tool_chain.get_node("non-existent")
        
        assert node is None
    
    def test_get_successors(self, simple_tool_chain):
        """Should be able to get successor nodes."""
        successors = simple_tool_chain.get_successors("input")
        
        assert len(successors) == 1
        assert successors[0].id == "process"
    
    def test_get_predecessors(self, simple_tool_chain):
        """Should be able to get predecessor nodes."""
        predecessors = simple_tool_chain.get_predecessors("process")
        
        assert len(predecessors) == 1
        assert predecessors[0].id == "input"
    
    def test_topological_sort(self, simple_tool_chain):
        """Nodes should be sorted in topological order."""
        sorted_nodes = simple_tool_chain.topological_sort()
        
        # Should be in order: input -> process -> output
        node_ids = [node.id for node in sorted_nodes]
        assert node_ids.index("input") < node_ids.index("process")
        assert node_ids.index("process") < node_ids.index("output")


class TestOrchestrationEngine:
    """Tests for OrchestrationEngine."""
    
    @pytest.mark.asyncio
    async def test_execute_simple_chain(self, orchestration_engine, simple_tool_chain):
        """Should be able to execute a simple chain."""
        context = await orchestration_engine.execute_chain(
            simple_tool_chain,
            initial_inputs={"test": "value"}
        )
        
        assert context is not None
        assert context.chain_id == "test-chain"
        assert context.status == ChainStatus.COMPLETED
        assert len(context.node_results) > 0
    
    @pytest.mark.asyncio
    async def test_get_execution(self, orchestration_engine, simple_tool_chain):
        """Should be able to get an execution by ID."""
        # First execute the chain
        context = await orchestration_engine.execute_chain(
            simple_tool_chain,
            initial_inputs={"test": "value"}
        )
        
        # Then get it by ID
        retrieved_context = orchestration_engine.get_execution(context.execution_id)
        
        assert retrieved_context is not None
        assert retrieved_context.execution_id == context.execution_id
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, orchestration_engine, simple_tool_chain):
        """Should be able to cancel an execution."""
        # First execute the chain
        context = await orchestration_engine.execute_chain(
            simple_tool_chain,
            initial_inputs={"test": "value"}
        )
        
        # Cancel it
        success = orchestration_engine.cancel_execution(context.execution_id)
        
        assert success is True
    
    def test_list_active_executions(self, orchestration_engine):
        """Should be able to list active execution IDs."""
        active_ids = orchestration_engine.list_active_executions()
        
        assert isinstance(active_ids, list)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_chain(self, orchestration_engine):
        """Executing an invalid chain should raise an error."""
        invalid_chain = ToolChain(
            id="invalid-chain",
            name="Invalid Chain",
            nodes=[],
            edges=[]
        )
        
        with pytest.raises(ValueError):
            await orchestration_engine.execute_chain(
                invalid_chain,
                initial_inputs={}
            )


class TestExecutionContext:
    """Tests for ExecutionContext."""
    
    def test_create_execution_context(self):
        """Should be able to create an execution context."""
        context = ExecutionContext(
            execution_id="test-123",
            chain_id="test-chain"
        )
        
        assert context.execution_id == "test-123"
        assert context.chain_id == "test-chain"
        assert context.status == ChainStatus.RUNNING
        assert isinstance(context.node_results, dict)
        assert isinstance(context.variables, dict)
        assert isinstance(context.start_time, datetime)
    
    def test_execution_context_initial_state(self):
        """Initial state should have empty results and variables."""
        context = ExecutionContext(
            execution_id="test-123",
            chain_id="test-chain"
        )
        
        assert len(context.node_results) == 0
        assert len(context.variables) == 0
        assert len(context.errors) == 0
        assert context.end_time is None


class TestNodeExecutionResult:
    """Tests for NodeExecutionResult."""
    
    def test_create_success_result(self):
        """Should be able to create a success result."""
        result = NodeExecutionResult(
            node_id="test-node",
            status="success",
            output={"data": "value"},
            start_time=datetime.utcnow()
        )
        
        assert result.node_id == "test-node"
        assert result.status == "success"
        assert result.output == {"data": "value"}
        assert result.error is None
    
    def test_create_error_result(self):
        """Should be able to create an error result."""
        result = NodeExecutionResult(
            node_id="test-node",
            status="failed",
            error="Something went wrong",
            start_time=datetime.utcnow()
        )
        
        assert result.node_id == "test-node"
        assert result.status == "failed"
        assert result.error == "Something went wrong"
        assert result.output is None
