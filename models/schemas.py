"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class NodeType(str, Enum):
    """Types of nodes in the call graph"""
    CONTROLLER = "controller"
    SERVICE = "service"
    SERVICE_IMPL = "service_impl"
    FACADE = "facade"
    DAO = "dao"
    HELPER = "helper"
    UTILITY = "utility"

class MethodParameter(BaseModel):
    """Represents a method parameter"""
    name: str
    type: str
    annotations: List[str] = []

class MethodSignature(BaseModel):
    """Represents a method signature"""
    name: str
    return_type: str
    parameters: List[MethodParameter]
    modifiers: List[str] = []
    annotations: List[str] = []
    throws: List[str] = []

class MethodNode(BaseModel):
    """Represents a method node in the call graph"""
    id: str = Field(..., description="Unique identifier for the node")
    name: str = Field(..., description="Method name")
    class_name: str = Field(..., description="Fully qualified class name")
    node_type: NodeType = Field(..., description="Type of node")
    signature: MethodSignature
    source_code: Optional[str] = Field(None, description="Java source code")
    converted_code: Optional[str] = Field(None, description="Python converted code")
    file_path: str = Field(..., description="Path to source file")
    line_number: int = Field(..., description="Starting line number")
    dependencies: List[str] = Field(default_factory=list, description="List of method IDs this method calls")

class CallEdge(BaseModel):
    """Represents an edge in the call graph"""
    source: str = Field(..., description="Source method ID")
    target: str = Field(..., description="Target method ID")
    call_type: str = Field(..., description="Type of call (direct, interface, etc.)")

class CallGraph(BaseModel):
    """Represents the complete call graph for an API"""
    api_name: str
    service_name: str
    entry_point: str = Field(..., description="Entry point method ID")
    nodes: List[MethodNode]
    edges: List[CallEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceInfo(BaseModel):
    """Information about a service"""
    name: str
    interface_path: str
    implementation_path: str
    api_count: int
    apis: List[str] = []

class ServiceListResponse(BaseModel):
    """Response for service listing"""
    services: List[ServiceInfo]
    total_count: int

class APIInfo(BaseModel):
    """Information about an API method"""
    name: str
    signature: MethodSignature
    service_name: str
    description: Optional[str] = None

class APIListResponse(BaseModel):
    """Response for API listing"""
    service_name: str
    apis: List[APIInfo]
    total_count: int

class MigrationRequest(BaseModel):
    """Request to migrate an API"""
    service_name: str
    api_name: str
    include_tests: bool = False
    llm_model: Optional[str] = "gpt-4"

class MigrationStatus(str, Enum):
    """Status of migration"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"

class MigrationResponse(BaseModel):
    """Response for migration request"""
    migration_id: str
    status: MigrationStatus
    call_graph: Optional[CallGraph] = None
    message: str
    errors: List[str] = Field(default_factory=list)

class CodeConversionRequest(BaseModel):
    """Request to convert Java code to Python"""
    java_code: str
    context: Optional[Dict[str, Any]] = None
    llm_model: Optional[str] = "gpt-4"

class CodeConversionResponse(BaseModel):
    """Response for code conversion"""
    python_code: str
    explanation: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
