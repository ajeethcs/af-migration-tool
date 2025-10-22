"""
Node-by-Node Converter

Converts call graphs node-by-node to stay within LLM token limits.
This is the solution to "token becomes too large" problem.
"""
import json
import re
from typing import Dict, List, Optional
from pathlib import Path


class NodeByNodeConverter:
    """
    Converts call graph node-by-node to avoid token limit issues
    
    Instead of sending entire call graph (100K+ tokens), this sends
    one node at a time (10-15K tokens each).
    """
    
    def __init__(self, max_tokens_per_call: int = 30000):
        """
        Initialize converter
        
        Args:
            max_tokens_per_call: Maximum tokens to send in single LLM call
        """
        self.max_tokens_per_call = max_tokens_per_call
        self.converted_nodes = {}
    
    def convert_call_graph(
        self, 
        call_graph: Dict,
        llm_converter_func: Optional[callable] = None
    ) -> Dict:
        """
        Convert entire call graph by processing nodes individually
        
        Args:
            call_graph: Enhanced call graph with metadata
            llm_converter_func: Function to call LLM (optional, for testing)
            
        Returns:
            Complete API configuration JSON
        """
        print("\n" + "="*70)
        print("NODE-BY-NODE CONVERSION")
        print("="*70)
        
        api_config = {
            "name": call_graph.get("api_name", "unknown"),
            "active": True,
            "nodes": {},
            "connections": {}
        }
        
        nodes = call_graph.get("nodes", [])
        
        if not nodes:
            raise ValueError("Call graph has no nodes!")
        
        print(f"\nTotal nodes to convert: {len(nodes)}")
        print(f"Max tokens per call: {self.max_tokens_per_call:,}")
        
        # Step 1: Convert API node (first node)
        print(f"\n{'='*70}")
        print("STEP 1: Converting API Node")
        print(f"{'='*70}")
        
        api_node = self._convert_api_node(nodes[0], call_graph)
        api_config["nodes"]["__NODE1__"] = api_node
        print("✓ API node converted")
        
        # Step 2: Convert each code node individually
        for i, node in enumerate(nodes[1:], start=2):
            node_name = node.get("signature", {}).get("name", "unknown")
            
            print(f"\n{'='*70}")
            print(f"STEP {i}: Converting Code Node - {node_name}")
            print(f"{'='*70}")
            
            # Build minimal context for this node
            context = self._build_node_context(node, call_graph, api_config)
            
            # Estimate tokens
            estimated_tokens = self._estimate_tokens(context)
            print(f"  Estimated tokens: {estimated_tokens:,}")
            
            # Compress if needed
            if estimated_tokens > self.max_tokens_per_call:
                print(f"  ⚠️  Exceeds limit! Compressing...")
                context = self._compress_context(context)
                estimated_tokens = self._estimate_tokens(context)
                print(f"  Compressed tokens: {estimated_tokens:,}")
                
                if estimated_tokens > self.max_tokens_per_call:
                    print(f"  ⚠️  Still too large! Using aggressive compression...")
                    context = self._aggressive_compress(context)
                    estimated_tokens = self._estimate_tokens(context)
                    print(f"  Final tokens: {estimated_tokens:,}")
            
            # Convert this node
            if llm_converter_func:
                converted = llm_converter_func(context, i)
            else:
                # Generate placeholder for testing
                converted = self._generate_placeholder_node(node, i)
            
            api_config["nodes"][f"__NODE{i}__"] = converted
            
            # Add connection from previous node
            api_config["connections"][f"edge-__NODE{i-1}__-__NODE{i}__"] = {
                "id": f"edge-__NODE{i-1}__-__NODE{i}__",
                "source": f"__NODE{i-1}__",
                "target": f"__NODE{i}__"
            }
            
            print(f"  ✓ Node {i} converted")
        
        print(f"\n{'='*70}")
        print("CONVERSION COMPLETE")
        print(f"{'='*70}")
        print(f"  Total nodes: {len(api_config['nodes'])}")
        print(f"  Total connections: {len(api_config['connections'])}")
        print(f"{'='*70}\n")
        
        return api_config
    
    def _build_node_context(
        self, 
        node: Dict, 
        call_graph: Dict, 
        api_config: Dict
    ) -> Dict:
        """
        Build minimal context for converting a single node
        
        Only includes:
        - This node's source code
        - Metadata used in THIS node only
        - Previous nodes for data flow context
        - Essential conversion hints
        """
        # Compress source code
        source_code = node.get("source_code", "")
        compressed_code = self._compress_source_code(source_code)
        
        # Get only metadata used in THIS node
        node_metadata = self._get_node_metadata(node, call_graph.get("metadata", {}))
        
        # Build context
        context = {
            "node": {
                "name": node.get("signature", {}).get("name", "unknown"),
                "signature": node.get("signature", {}),
                "source_code": compressed_code,
                "node_type": node.get("node_type", "code"),
                "logic_annotations": node.get("logic_annotations", {})
            },
            "metadata": node_metadata,
            "previous_nodes_summary": self._summarize_previous_nodes(api_config["nodes"]),
            "conversion_hints": self._get_essential_hints(call_graph.get("metadata", {}))
        }
        
        return context
    
    def _get_node_metadata(self, node: Dict, full_metadata: Dict) -> Dict:
        """
        Extract only metadata needed for this specific node
        """
        source_code = node.get("source_code", "")
        
        node_metadata = {
            "entities": {},
            "enums": {},
            "helper_methods": {},
            "database": {
                "dialect": full_metadata.get("database", {}).get("dialect", "mysql")
            }
        }
        
        # Only include entities referenced in this node
        for entity_name, entity_data in full_metadata.get("entities", {}).items():
            if entity_name in source_code:
                node_metadata["entities"][entity_name] = {
                    "table_name": entity_data.get("table_name", ""),
                    "fields": entity_data.get("fields", {})
                }
        
        # Only include enums referenced in this node
        for enum_name, enum_data in full_metadata.get("enums", {}).items():
            if enum_name in source_code:
                node_metadata["enums"][enum_name] = enum_data
        
        # Only include helpers called in this node
        for helper_name, helper_data in full_metadata.get("helper_methods", {}).items():
            if helper_name in source_code:
                node_metadata["helper_methods"][helper_name] = {
                    "signature": helper_data.get("signature", ""),
                    "source_code": self._compress_source_code(
                        helper_data.get("source_code", "")
                    )
                }
        
        return node_metadata
    
    def _summarize_previous_nodes(self, previous_nodes: Dict) -> List[Dict]:
        """
        Create compact summary of previous nodes for context
        """
        summary = []
        
        for node_id, node_data in previous_nodes.items():
            summary.append({
                "id": node_id,
                "name": node_data.get("nodeName", "unknown"),
                "type": node_data.get("type", "code"),
                "purpose": self._infer_node_purpose(node_data)
            })
        
        return summary
    
    def _infer_node_purpose(self, node_data: Dict) -> str:
        """
        Infer the purpose of a node from its name/prompt
        """
        name = node_data.get("nodeName", "").lower()
        prompt = node_data.get("data", {}).get("parameters", {}).get("prompt", "").lower()
        
        if "validate" in name or "validate" in prompt:
            return "validation"
        elif "query" in name or "database" in prompt:
            return "database_query"
        elif "format" in name or "response" in prompt:
            return "formatting"
        else:
            return "business_logic"
    
    def _get_essential_hints(self, full_metadata: Dict) -> Dict:
        """
        Get only essential conversion hints (not full hints)
        """
        hints = full_metadata.get("conversion_hints", {})
        
        return {
            "critical_rules": hints.get("critical_rules", []),
            "database_dialect": hints.get("database", {}).get("dialect", "mysql")
        }
    
    def _compress_source_code(self, source_code: str) -> str:
        """
        Remove unnecessary content from source code
        """
        if not source_code:
            return ""
        
        # Remove single-line comments
        source_code = re.sub(r'//.*?$', '', source_code, flags=re.MULTILINE)
        
        # Remove multi-line comments (but keep Javadoc)
        source_code = re.sub(r'/\*(?!\*).*?\*/', '', source_code, flags=re.DOTALL)
        
        # Remove excessive whitespace
        source_code = re.sub(r'\n\s*\n+', '\n', source_code)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.rstrip() for line in source_code.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def _compress_context(self, context: Dict) -> Dict:
        """
        Further compress context if still too large
        """
        # Simplify logic annotations
        if "logic_annotations" in context.get("node", {}):
            annotations = context["node"]["logic_annotations"]
            context["node"]["logic_annotations"] = {
                "complexity_score": annotations.get("complexity_score", 0),
                "patterns": [p.get("type", "") for p in annotations.get("patterns", [])],
                "recommendations": annotations.get("recommendations", [])[:3]  # Top 3 only
            }
        
        # Keep only critical conversion hints
        if "conversion_hints" in context:
            context["conversion_hints"] = {
                "critical_rules": context["conversion_hints"].get("critical_rules", [])[:5]
            }
        
        # Compress helper source code
        for helper_data in context.get("metadata", {}).get("helper_methods", {}).values():
            if len(helper_data.get("source_code", "")) > 500:
                # Keep only first 500 chars + signature
                helper_data["source_code"] = helper_data.get("signature", "")
        
        return context
    
    def _aggressive_compress(self, context: Dict) -> Dict:
        """
        Aggressive compression for very large nodes
        """
        # Remove logic annotations entirely
        if "logic_annotations" in context.get("node", {}):
            context["node"]["logic_annotations"] = {
                "complexity_score": context["node"]["logic_annotations"].get("complexity_score", 0)
            }
        
        # Remove previous nodes summary
        context["previous_nodes_summary"] = []
        
        # Remove helper implementations, keep only signatures
        for helper_data in context.get("metadata", {}).get("helper_methods", {}).values():
            helper_data["source_code"] = ""
        
        # Truncate source code if extremely long
        if len(context["node"]["source_code"]) > 2000:
            context["node"]["source_code"] = context["node"]["source_code"][:2000] + "\n// ... truncated ..."
        
        return context
    
    def _estimate_tokens(self, context: Dict) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English)
        """
        json_str = json.dumps(context)
        return len(json_str) // 4
    
    def _convert_api_node(self, node: Dict, call_graph: Dict) -> Dict:
        """
        Convert the API node (no LLM needed, straightforward mapping)
        """
        api_name = call_graph.get("api_name", "unknown")
        
        # Infer HTTP method from method name
        method_name = node.get("signature", {}).get("name", "").lower()
        if any(x in method_name for x in ["get", "find", "search", "list"]):
            http_method = "GET"
        elif any(x in method_name for x in ["create", "add", "insert"]):
            http_method = "POST"
        elif any(x in method_name for x in ["update", "modify", "edit"]):
            http_method = "PUT"
        elif any(x in method_name for x in ["delete", "remove"]):
            http_method = "DELETE"
        else:
            http_method = "POST"  # Default
        
        # Extract parameters
        params = node.get("signature", {}).get("parameters", [])
        query_params = []
        
        for param in params:
            query_params.append({
                "key": param.get("name", ""),
                "value": self._get_default_value(param.get("type", ""))
            })
        
        return {
            "id": "__NODE1__",
            "type": "api",
            "position": {"x": 0, "y": 150},
            "data": {
                "label": "API",
                "isLastNode": False,
                "parameters": {
                    "apiName": api_name,
                    "httpMethod": http_method,
                    "path": f"/{api_name}",
                    "apiDescription": f"Migrated from Java SOAP service",
                    "queryParams": query_params if http_method == "GET" else [],
                    "formdataParams": query_params if http_method != "GET" else [],
                    "headerParams": [],
                    "isAuthorizationEnabled": True,
                    "authentication": {"credentialId": None},
                    "exceptionHandlers": [
                        {
                            "exceptionCategoryId": 0,
                            "name": "All exceptions",
                            "properties": {
                                "errorMessage": "An error occurred",
                                "exceptionName": "AllExceptions"
                            }
                        }
                    ]
                }
            },
            "nodeName": api_name,
            "objectName": api_name.lower()
        }
    
    def _get_default_value(self, param_type: str) -> str:
        """
        Get default value for parameter type
        """
        type_map = {
            "int": "0",
            "long": "0",
            "double": "0.0",
            "float": "0.0",
            "boolean": "false",
            "String": "",
            "Date": "2024-01-01"
        }
        return type_map.get(param_type, "")
    
    def _generate_placeholder_node(self, node: Dict, node_number: int) -> Dict:
        """
        Generate a placeholder node for testing (when no LLM converter provided)
        """
        node_name = node.get("signature", {}).get("name", f"node{node_number}")
        
        return {
            "id": f"__NODE{node_number}__",
            "type": "code",
            "position": {"x": (node_number - 1) * 250, "y": 150},
            "data": {
                "label": "Code",
                "isLastNode": False,
                "parameters": {
                    "language": "python",
                    "prompt": f"Convert {node_name} to Python",
                    "code": f"# TODO: Convert {node_name}\npass"
                }
            },
            "nodeName": node_name,
            "objectName": node_name.lower()
        }


def compress_source_code(source_code: str) -> str:
    """
    Standalone function to compress source code
    """
    converter = NodeByNodeConverter()
    return converter._compress_source_code(source_code)


if __name__ == "__main__":
    # Test the converter
    print("Testing NodeByNodeConverter...\n")
    
    # Create a mock call graph
    mock_call_graph = {
        "api_name": "getClaims",
        "service_name": "ClaimService",
        "nodes": [
            {
                "signature": {"name": "getClaims", "parameters": [{"name": "clinicId", "type": "int"}]},
                "source_code": "public List<Claim> getClaims(int clinicId) { return null; }",
                "node_type": "service_impl"
            },
            {
                "signature": {"name": "validateInput"},
                "source_code": "private void validateInput(int id) { if (id == 0) throw new Exception(); }",
                "node_type": "helper",
                "logic_annotations": {"complexity_score": 3}
            }
        ],
        "metadata": {
            "entities": {
                "MediumClaim": {
                    "table_name": "CLAIM",
                    "fields": {"C_ID": {"column": "CLINIC_ID"}}
                }
            },
            "enums": {},
            "helper_methods": {},
            "database": {"dialect": "mysql"}
        }
    }
    
    # Test conversion
    converter = NodeByNodeConverter(max_tokens_per_call=10000)
    result = converter.convert_call_graph(mock_call_graph)
    
    print("\nResult:")
    print(json.dumps(result, indent=2))
