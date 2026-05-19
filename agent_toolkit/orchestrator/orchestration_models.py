"""Models for tool chain orchestration."""

from datetime import datetime
from typing import Any, Optional, Dict, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    """Types of nodes in a tool chain."""
    TOOL = "tool"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    INPUT = "input"
    OUTPUT = "output"


class ExecutionMode(str, Enum):
    """Execution mode for tool chains."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DAG = "dag"


class ChainStatus(str, Enum):
    """Status of a tool chain execution."""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryPolicy(BaseModel):
    """Retry policy for node execution."""
    max_attempts: int = Field(1, ge=1, le=10)
    retry_delay: float = Field(1.0, ge=0)
    backoff_multiplier: float = Field(2.0, ge=1.0)
    retry_on_errors: List[str] = Field(default_factory=lambda: ["*"])


class ChainNode(BaseModel):
    """A node in a tool chain."""
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type")
    name: str = Field(..., description="Node name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    retry_policy: Optional[RetryPolicy] = Field(None, description="Retry policy")
    timeout: Optional[int] = Field(None, ge=1, description="Execution timeout in seconds")
    condition: Optional[str] = Field(None, description="Condition expression")
    inputs: Dict[str, str] = Field(default_factory=dict, description="Input mappings")
    outputs: List[str] = Field(default_factory=list, description="Output variable names")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate node ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Node ID must be alphanumeric with underscores/hyphens')
        return v


class ChainEdge(BaseModel):
    """An edge connecting two nodes in a tool chain."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    condition: Optional[str] = Field(None, description="Condition for edge traversal")
    priority: int = Field(0, description="Edge priority")
    label: Optional[str] = Field(None, description="Edge label")


class ToolChain(BaseModel):
    """A tool chain definition."""
    id: str = Field(..., min_length=1, description="Unique chain identifier")
    name: str = Field(..., description="Chain name")
    description: Optional[str] = Field(None, description="Chain description")
    version: str = Field("1.0.0", description="Chain version")
    nodes: List[ChainNode] = Field(default_factory=list, description="Chain nodes")
    edges: List[ChainEdge] = Field(default_factory=list, description="Chain edges")
    execution_mode: ExecutionMode = Field(ExecutionMode.SEQUENTIAL, description="Execution mode")
    status: ChainStatus = Field(ChainStatus.DRAFT, description="Chain status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Creator identifier")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate chain ID format."""
        if not v or not v.strip():
            raise ValueError('Chain ID cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Chain ID must be alphanumeric with underscores/hyphens')
        return v

    def validate(self) -> tuple[bool, List[str]]:
        """Validate the tool chain structure."""
        errors = []

        node_ids = {node.id for node in self.nodes}

        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge references unknown source node: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge references unknown target node: {edge.target}")

        if self.execution_mode == ExecutionMode.PARALLEL:
            for node in self.nodes:
                if node.type == NodeType.LOOP:
                    errors.append("Loop nodes not allowed in parallel execution mode")

        return len(errors) == 0, errors

    def get_node(self, node_id: str) -> Optional[ChainNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_successors(self, node_id: str) -> List[ChainNode]:
        """Get successor nodes of a given node."""
        successor_ids = {edge.target for edge in self.edges if edge.source == node_id}
        return [node for node in self.nodes if node.id in successor_ids]

    def get_predecessors(self, node_id: str) -> List[ChainNode]:
        """Get predecessor nodes of a given node."""
        predecessor_ids = {edge.source for edge in self.edges if edge.target == node_id}
        return [node for node in self.nodes if node.id in predecessor_ids]

    def topological_sort(self) -> List[ChainNode]:
        """Return nodes in topological order."""
        in_degree = {node.id: 0 for node in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1

        queue = [node for node in self.nodes if in_degree[node.id] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for successor in self.get_successors(node.id):
                in_degree[successor.id] -= 1
                if in_degree[successor.id] == 0:
                    queue.append(successor)

        return result


class ExecutionContext(BaseModel):
    """Context for chain execution."""
    execution_id: str
    chain_id: str
    status: ChainStatus = ChainStatus.RUNNING
    node_results: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeExecutionResult(BaseModel):
    """Result of a node execution."""
    node_id: str
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# 别名以提供更好的API兼容性
ChainDefinition = ToolChain
