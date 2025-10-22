"""
Call graph builder for tracing API execution flow
"""
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import re
import uuid
import os

from config import (
    SERVICES_IMPL_PATH, FACADE_PATH, DAO_PATH,
    ALLOFACTOR_SRC, ALLOFACTORSERVICE_SRC
)
from core.java_parser import JavaParser
from models.schemas import (
    CallGraph, MethodNode, CallEdge, NodeType,
    MethodSignature, MethodParameter
)

class CallGraphBuilder:
    """Builds call graphs for API methods"""
    
    def __init__(self):
        self.visited_methods: Set[str] = set()
        self.nodes: List[MethodNode] = []
        self.edges: List[CallEdge] = []
        self.method_cache: Dict[str, Dict] = {}
    
    def build_call_graph(self, service_name: str, api_name: str) -> CallGraph:
        """Build a complete call graph for an API"""
        self.visited_methods.clear()
        self.nodes.clear()
        self.edges.clear()
        self.method_cache.clear()
        
        # Find the entry point (service implementation method)
        impl_file = SERVICES_IMPL_PATH / f"{service_name}Impl.java"
        
        if not impl_file.exists():
            raise FileNotFoundError(f"Service implementation not found: {impl_file}")
        
        # Parse the implementation
        parser = JavaParser(impl_file)
        methods = parser.get_methods()
        
        # Find the API method
        entry_method = None
        for method in methods:
            if method["name"] == api_name:
                entry_method = method
                break
        
        if not entry_method:
            raise ValueError(f"API method '{api_name}' not found in {service_name}")
        
        # Create entry node
        entry_node_id = self._create_node(
            entry_method,
            NodeType.SERVICE_IMPL,
            str(impl_file),
            parser.get_fully_qualified_name()
        )
        
        # Recursively build the call graph
        self._trace_method_calls(entry_method, entry_node_id, parser)
        
        return CallGraph(
            api_name=api_name,
            service_name=service_name,
            entry_point=entry_node_id,
            nodes=self.nodes,
            edges=self.edges,
            metadata={
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges)
            }
        )
    
    def _create_node(
        self,
        method_info: Dict,
        node_type: NodeType,
        file_path: str,
        class_name: str
    ) -> str:
        """Create a method node"""
        node_id = f"{class_name}.{method_info['name']}_{uuid.uuid4().hex[:8]}"
        
        # Create method signature
        parameters = [
            MethodParameter(
                name=p["name"],
                type=p["type"],
                annotations=p.get("annotations", [])
            )
            for p in method_info.get("parameters", [])
        ]
        
        signature = MethodSignature(
            name=method_info["name"],
            return_type=method_info.get("return_type", "void"),
            parameters=parameters,
            modifiers=method_info.get("modifiers", []),
            annotations=method_info.get("annotations", []),
            throws=method_info.get("throws", [])
        )
        
        node = MethodNode(
            id=node_id,
            name=method_info["name"],
            class_name=class_name,
            node_type=node_type,
            signature=signature,
            source_code=method_info.get("source_code", ""),
            file_path=file_path,
            line_number=method_info.get("line_number", 0),
            dependencies=[]
        )
        
        self.nodes.append(node)
        return node_id
    
    def _trace_method_calls(
        self,
        method_info: Dict,
        source_node_id: str,
        parser: JavaParser
    ):
        """Recursively trace method calls"""
        source_code = method_info.get("source_code", "")
        if not source_code:
            return
        
        # Find method calls in the source
        method_calls = self._extract_method_calls(source_code)
        
        for call_info in method_calls:
            target_method = self._resolve_method_call(call_info, parser)
            
            if target_method:
                target_node_id = self._process_called_method(target_method)
                
                if target_node_id:
                    # Create edge
                    edge = CallEdge(
                        source=source_node_id,
                        target=target_node_id,
                        call_type=call_info.get("type", "direct")
                    )
                    self.edges.append(edge)
                    
                    # Update dependencies
                    for node in self.nodes:
                        if node.id == source_node_id:
                            node.dependencies.append(target_node_id)
                            break
    
    def _extract_method_calls(self, source_code: str) -> List[Dict]:
        """Extract method calls from source code"""
        method_calls = []
        
        # Debug: Check if we should print debug info
        debug = os.getenv('DEBUG_CALL_GRAPH', '').lower() in ('1', 'true', 'yes')
        
        # Pattern for daoFacade calls
        facade_pattern = r'daoFacade\.(\w+)\s*\('
        for match in re.finditer(facade_pattern, source_code):
            method_calls.append({
                "object": "daoFacade",
                "method": match.group(1),
                "type": "facade"
            })
            if debug:
                print(f"  [DEBUG] Found facade call: daoFacade.{match.group(1)}()")
        
        # Pattern for DAO field calls (e.g., this.mediumClaimBODao.method())
        dao_field_pattern = r'this\.(\w+Dao)\.(\w+)\s*\('
        for match in re.finditer(dao_field_pattern, source_code):
            method_calls.append({
                "object": match.group(1),
                "method": match.group(2),
                "type": "dao_field"
            })
            if debug:
                print(f"  [DEBUG] Found DAO field call: this.{match.group(1)}.{match.group(2)}()")
        
        # Pattern for direct DAO calls (e.g., claimDao.method())
        dao_direct_pattern = r'(?<!this\.)\b(\w+Dao)\.(\w+)\s*\('
        for match in re.finditer(dao_direct_pattern, source_code):
            method_calls.append({
                "object": match.group(1),
                "method": match.group(2),
                "type": "dao_direct"
            })
        
        # Pattern for helper calls
        helper_pattern = r'(\w+Helper)\.(\w+)\s*\('
        for match in re.finditer(helper_pattern, source_code):
            method_calls.append({
                "object": match.group(1),
                "method": match.group(2),
                "type": "helper"
            })
        
        # Pattern for this.method() calls
        this_pattern = r'this\.(\w+)\s*\('
        for match in re.finditer(this_pattern, source_code):
            # Skip if it's a DAO field call (already captured above)
            if not match.group(1).endswith('Dao'):
                method_calls.append({
                    "object": "this",
                    "method": match.group(1),
                    "type": "internal"
                })
        
        return method_calls
    
    def _resolve_method_call(
        self,
        call_info: Dict,
        current_parser: JavaParser
    ) -> Optional[Dict]:
        """Resolve a method call to its definition"""
        method_name = call_info["method"]
        call_type = call_info["type"]
        
        if call_type == "facade":
            return self._find_facade_method(method_name)
        elif call_type == "dao_field" or call_type == "dao_direct":
            return self._find_dao_method(call_info["object"], method_name, current_parser)
        elif call_type == "helper":
            return self._find_helper_method(call_info["object"], method_name)
        elif call_type == "internal":
            # Look in the same class
            methods = current_parser.get_methods()
            for method in methods:
                if method["name"] == method_name:
                    # Determine node type based on current context
                    node_type = self._determine_node_type(current_parser)
                    return {
                        "method_info": method,
                        "parser": current_parser,
                        "node_type": node_type
                    }
        
        return None
    
    def _find_facade_method(self, method_name: str) -> Optional[Dict]:
        """Find a method in the DaoFacade"""
        facade_impl_file = FACADE_PATH / "DaoFacadeImpl.java"
        
        if not facade_impl_file.exists():
            return None
        
        parser = JavaParser(facade_impl_file)
        methods = parser.get_methods()
        
        for method in methods:
            if method["name"] == method_name:
                return {
                    "method_info": method,
                    "parser": parser,
                    "node_type": NodeType.FACADE
                }
        
        return None
    
    def _find_helper_method(self, helper_class: str, method_name: str) -> Optional[Dict]:
        """Find a method in a helper class"""
        # Look for helper in the impl directory
        helper_file = SERVICES_IMPL_PATH / f"{helper_class}.java"
        
        if not helper_file.exists():
            return None
        
        parser = JavaParser(helper_file)
        methods = parser.get_methods()
        
        for method in methods:
            if method["name"] == method_name:
                return {
                    "method_info": method,
                    "parser": parser,
                    "node_type": NodeType.HELPER
                }
        
        return None
    
    def _find_dao_method(self, dao_field: str, method_name: str, current_parser: JavaParser) -> Optional[Dict]:
        """Find a method in a DAO implementation"""
        debug = os.getenv('DEBUG_CALL_GRAPH', '').lower() in ('1', 'true', 'yes')
        
        if debug:
            print(f"  [DEBUG] Resolving DAO: {dao_field}.{method_name}()")
        
        # First, try to find the DAO class name from the field
        dao_class_name = self._resolve_dao_class(dao_field, current_parser)
        
        if debug:
            print(f"  [DEBUG]   Resolved from fields: {dao_class_name}")
        
        if not dao_class_name:
            # Try common naming patterns
            # e.g., mediumClaimBODao -> MediumClaimBODaoImpl
            dao_class_name = dao_field[0].upper() + dao_field[1:] + "Impl"
            if debug:
                print(f"  [DEBUG]   Using naming convention: {dao_class_name}")
        
        # Try multiple file name patterns and locations
        file_attempts = []
        
        # Build list of filenames to try
        filenames = []
        if dao_class_name and not dao_class_name.endswith("Impl"):
            filenames.append(f"{dao_class_name}Impl.java")
        if dao_class_name:
            filenames.append(f"{dao_class_name}.java")
        filenames.append(f"{dao_field[0].upper() + dao_field[1:]}Impl.java")
        filenames.append(f"{dao_field[0].upper() + dao_field[1:]}.java")
        
        # Try Hibernate implementation
        if dao_class_name:
            filenames.append(f"Hibernate{dao_class_name}.java")
        filenames.append(f"Hibernate{dao_field[0].upper() + dao_field[1:]}.java")
        
        # Build list of locations to check
        locations = [
            DAO_PATH / "impl",           # impl subdirectory
            DAO_PATH / "hibernate",      # hibernate subdirectory
            DAO_PATH,                    # parent dao directory
        ]
        
        # Try all combinations
        dao_impl_file = None
        for location in locations:
            for filename in filenames:
                test_file = location / filename
                if debug:
                    print(f"  [DEBUG]   Trying: {location.name}/{filename} - Exists: {test_file.exists()}")
                if test_file.exists():
                    dao_impl_file = test_file
                    if debug:
                        print(f"  [DEBUG]   ✓ Found file: {location.name}/{filename}")
                    break
            if dao_impl_file:
                break
        
        if dao_impl_file is None:
            if debug:
                print(f"  [DEBUG]   DAO file not found after trying all patterns!")
            return None
        
        if debug:
            print(f"  [DEBUG]   Parsing DAO file...")
        
        parser = JavaParser(dao_impl_file)
        methods = parser.get_methods()
        
        if debug:
            print(f"  [DEBUG]   Found {len(methods)} methods in DAO")
        
        for method in methods:
            if method["name"] == method_name:
                if debug:
                    print(f"  [DEBUG]   ✓ Found method {method_name} in DAO!")
                return {
                    "method_info": method,
                    "parser": parser,
                    "node_type": NodeType.DAO
                }
        
        if debug:
            print(f"  [DEBUG]   Method {method_name} not found in DAO")
            print(f"  [DEBUG]   Available methods: {[m['name'] for m in methods[:10]]}")
        
        return None
    
    def _resolve_dao_class(self, dao_field: str, parser: JavaParser) -> Optional[str]:
        """Resolve the actual DAO class name from a field name"""
        # Get fields from the current class
        fields = parser.get_fields()
        
        for field in fields:
            if field["name"] == dao_field:
                # Extract the class name from the type
                field_type = field["type"]
                # Handle generic types like List<Something>
                if "<" in field_type:
                    field_type = field_type.split("<")[0]
                return field_type
        
        return None
    
    def _determine_node_type(self, parser: JavaParser) -> NodeType:
        """Determine the node type based on the class name"""
        class_name = parser.get_fully_qualified_name()
        
        if "ServiceImpl" in class_name:
            return NodeType.SERVICE_IMPL
        elif "DaoFacadeImpl" in class_name or "DaoFacade" in class_name:
            return NodeType.FACADE
        elif "DaoImpl" in class_name or "Dao" in class_name:
            return NodeType.DAO
        elif "Helper" in class_name:
            return NodeType.HELPER
        else:
            return NodeType.UTILITY
    
    def _process_called_method(self, target_method: Dict) -> Optional[str]:
        """Process a called method and add it to the graph"""
        method_info = target_method["method_info"]
        parser = target_method["parser"]
        node_type = target_method["node_type"]
        
        # Create unique identifier for this method
        method_id = f"{parser.get_fully_qualified_name()}.{method_info['name']}"
        
        # Check if already visited
        if method_id in self.visited_methods:
            # Find and return existing node ID
            for node in self.nodes:
                if node.class_name == parser.get_fully_qualified_name() and node.name == method_info["name"]:
                    return node.id
            return None
        
        self.visited_methods.add(method_id)
        
        # Create node for this method
        node_id = self._create_node(
            method_info,
            node_type,
            str(parser.file_path),
            parser.get_fully_qualified_name()
        )
        
        # Recursively trace this method's calls (limit depth to avoid infinite recursion)
        if len(self.visited_methods) < 100:  # Depth limit
            self._trace_method_calls(method_info, node_id, parser)
        
        return node_id
