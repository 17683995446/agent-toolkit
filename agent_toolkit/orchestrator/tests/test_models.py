"""Unit tests for Orchestrator models."""

import pytest
from datetime import datetime
from typing import Any

from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainNode,
    ChainEdge,
    NodeType,
    ExecutionMode,
    ChainStatus,
)


class TestChainNode:
    """Test suite for ChainNode."""

    def test_node_creation(self) -> None:
        """Test creating a chain node."""
        node = ChainNode(
            id="node-1",
            type=NodeType.TOOL,
            config={"tool_id": "test-tool"},
            retry_policy={"max_attempts": 3}
        )
        
        assert node.id == "node-1"
        assert node.type == NodeType.TOOL
        assert node.config["tool_id"] == "test-tool"
        assert node.retry_policy["max_attempts"] == 3

    def test_node_with_timeout(self) -> None:
        """Test node with timeout configuration."""
        node = ChainNode(
            id="node-2",
            type=NodeType.TOOL,
            timeout=60
        )
        
        assert node.timeout == 60


class TestChainEdge:
    """Test suite for ChainEdge."""

    def test_edge_creation(self) -> None:
        """Test creating a chain edge."""
        edge = ChainEdge(
            source="node-1",
            target="node-2"
        )
        
        assert edge.source == "node-1"
        assert edge.target == "node-2"
        assert edge.condition is None

    def test_edge_with_condition(self) -> None:
        """Test edge with condition."""
        edge = ChainEdge(
            source="node-1",
            target="node-2",
            condition="result.status == 'success'"
        )
        
        assert edge.condition is not None
        assert "success" in edge.condition


class TestToolChain:
    """Test suite for ToolChain."""

    def test_chain_creation(self) -> None:
        """Test creating a tool chain."""
        nodes = [
            ChainNode(id="start", type=NodeType.TOOL),
            ChainNode(id="process", type=NodeType.TOOL),
            ChainNode(id="end", type=NodeType.TOOL),
        ]
        
        edges = [
            ChainEdge(source="start", target="process"),
            ChainEdge(source="process", target="end"),
        ]
        
        chain = ToolChain(
            id="chain-1",
            name="Test Chain",
            version="1.0.0",
            nodes=nodes,
            edges=edges
        )
        
        assert chain.id == "chain-1"
        assert len(chain.nodes) == 3
        assert len(chain.edges) == 2
        assert chain.status == ChainStatus.DRAFT

    def test_chain_with_metadata(self) -> None:
        """Test chain with metadata."""
        chain = ToolChain(
            id="chain-2",
            name="Complex Chain",
            version="2.0.0",
            nodes=[],
            edges=[],
            metadata={
                "author": "Test User",
                "description": "A complex chain"
            }
        )
        
        assert chain.metadata["author"] == "Test User"

    def test_chain_validation(self) -> None:
        """Test chain validation."""
        chain = ToolChain(
            id="chain-3",
            name="Invalid Chain",
            version="1.0.0",
            nodes=[],
            edges=[]
        )
        
        is_valid, errors = chain.validate()
        assert is_valid is False
        assert len(errors) > 0


class TestNodeType:
    """Test suite for NodeType enum."""

    def test_node_types(self) -> None:
        """Test NodeType enum values."""
        assert NodeType.TOOL.value == "tool"
        assert NodeType.CONDITION.value == "condition"
        assert NodeType.LOOP.value == "loop"
        assert NodeType.PARALLEL.value == "parallel"
        assert NodeType.MERGE.value == "merge"


class TestChainStatus:
    """Test suite for ChainStatus enum."""

    def test_chain_statuses(self) -> None:
        """Test ChainStatus enum values."""
        assert ChainStatus.DRAFT.value == "draft"
        assert ChainStatus.ACTIVE.value == "active"
        assert ChainStatus.PAUSED.value == "paused"
        assert ChainStatus.COMPLETED.value == "completed"
        assert ChainStatus.FAILED.value == "failed"
