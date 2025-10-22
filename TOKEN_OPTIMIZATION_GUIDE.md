# Token Optimization Guide

## The Problem

> **"When we add all these things, the token becomes too large and the API to LLM is being rejected"**

Even with metadata filtering, the complete call graph with:
- Multiple nodes with full source code
- Metadata (entities, enums, helpers)
- Logic annotations
- Conversion hints

Can easily exceed LLM token limits (e.g., GPT-4: 128K tokens, but expensive!)

---

## Solution Strategy

We need a **multi-layered approach**:

1. **Smart Chunking** - Split large APIs into smaller conversion units
2. **Progressive Enhancement** - Send only what's needed for each chunk
3. **Source Code Compression** - Remove unnecessary code
4. **Metadata Optimization** - Further reduce metadata size
5. **Streaming/Batching** - Process nodes in batches

---

## Strategy 1: Smart Chunking (RECOMMENDED)

### **Problem:**
Sending entire call graph (10+ nodes) at once = too many tokens

### **Solution:**
Convert **one node at a time** or in small groups

### **Implementation:**

```python
def convert_node_by_node(call_graph: Dict) -> Dict:
    """
    Convert each node individually instead of all at once
    """
    api_config = {
        "name": call_graph["api_name"],
        "nodes": {},
        "connections": {}
    }
    
    # 1. First, convert API node (always needed)
    api_node = call_graph["nodes"][0]  # First node is API
    api_config["nodes"]["__NODE1__"] = convert_api_node(api_node)
    
    # 2. Convert each code node individually
    for i, node in enumerate(call_graph["nodes"][1:], start=2):
        # Build minimal context for THIS node only
        node_context = {
            "node": node,
            "metadata": get_metadata_for_node(node, call_graph["metadata"]),
            "previous_nodes": api_config["nodes"]  # For data flow context
        }
        
        # Convert this single node
        converted = convert_single_node(node_context)
        api_config["nodes"][f"__NODE{i}__"] = converted
    
    return api_config
```

**Token Reduction:** 80-90% per LLM call

---

## Strategy 2: Progressive Enhancement

### **Problem:**
Sending ALL metadata even for a single node

### **Solution:**
Send only metadata **relevant to the current node**

### **Implementation:**

```python
def get_metadata_for_node(node: Dict, full_metadata: Dict) -> Dict:
    """
    Extract only metadata needed for this specific node
    """
    node_metadata = {
        "entities": {},
        "enums": {},
        "helper_methods": {},
        "database": full_metadata.get("database", {})
    }
    
    source_code = node.get("source_code", "")
    
    # Scan this node's source code
    for entity_name, entity_data in full_metadata.get("entities", {}).items():
        if entity_name in source_code:
            node_metadata["entities"][entity_name] = entity_data
    
    for enum_name, enum_data in full_metadata.get("enums", {}).items():
        if enum_name in source_code:
            node_metadata["enums"][enum_name] = enum_data
    
    # Only include helpers called in THIS node
    for helper_name, helper_data in full_metadata.get("helper_methods", {}).items():
        if helper_name in source_code:
            node_metadata["helper_methods"][helper_name] = helper_data
    
    return node_metadata
```

**Token Reduction:** 50-70% per node

---

## Strategy 3: Source Code Compression

### **Problem:**
Full Java source code includes comments, whitespace, imports

### **Solution:**
Strip unnecessary content before sending to LLM

### **Implementation:**

```python
import re

def compress_source_code(source_code: str) -> str:
    """
    Remove unnecessary content from source code
    """
    # Remove single-line comments
    source_code = re.sub(r'//.*?$', '', source_code, flags=re.MULTILINE)
    
    # Remove multi-line comments (but keep Javadoc for method signatures)
    source_code = re.sub(r'/\*(?!\*).*?\*/', '', source_code, flags=re.DOTALL)
    
    # Remove excessive whitespace
    source_code = re.sub(r'\n\s*\n', '\n', source_code)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in source_code.split('\n') if line.strip()]
    
    return '\n'.join(lines)
```

**Token Reduction:** 20-30%

---

## Strategy 4: Metadata Optimization

### **Problem:**
Even filtered metadata can be verbose

### **Solution:**
Send only essential fields

### **Implementation:**

```python
def optimize_metadata(metadata: Dict) -> Dict:
    """
    Keep only essential metadata fields
    """
    optimized = {
        "entities": {},
        "enums": metadata.get("enums", {}),  # Enums are small, keep as-is
        "database": {"dialect": metadata.get("database", {}).get("dialect", "mysql")}
    }
    
    # For entities, keep only table name and used fields
    for entity_name, entity_data in metadata.get("entities", {}).items():
        optimized["entities"][entity_name] = {
            "table_name": entity_data["table_name"],
            "fields": entity_data["fields"]  # Already filtered
        }
        # Remove: java_class, primary_key details if not needed
    
    return optimized
```

**Token Reduction:** 10-20%

---

## Strategy 5: Node-by-Node Conversion (BEST APPROACH)

### **Complete Implementation:**

```python
class NodeByNodeConverter:
    """
    Converts call graph node-by-node to stay within token limits
    """
    
    def __init__(self, max_tokens_per_call: int = 30000):
        self.max_tokens_per_call = max_tokens_per_call
        self.converted_nodes = {}
    
    def convert_call_graph(self, call_graph: Dict) -> Dict:
        """
        Convert entire call graph by processing nodes individually
        """
        print("\n🔄 Starting node-by-node conversion...")
        
        api_config = {
            "name": call_graph["api_name"],
            "active": True,
            "nodes": {},
            "connections": {}
        }
        
        nodes = call_graph.get("nodes", [])
        
        # Step 1: Convert API node
        print(f"\n1. Converting API node...")
        api_node = self._convert_api_node(nodes[0], call_graph)
        api_config["nodes"]["__NODE1__"] = api_node
        
        # Step 2: Convert each code node
        for i, node in enumerate(nodes[1:], start=2):
            print(f"\n{i}. Converting node: {node.get('signature', {}).get('name', 'unknown')}...")
            
            # Build minimal context for this node
            context = self._build_node_context(node, call_graph, api_config)
            
            # Estimate tokens
            estimated_tokens = self._estimate_tokens(context)
            print(f"   Estimated tokens: {estimated_tokens:,}")
            
            if estimated_tokens > self.max_tokens_per_call:
                print(f"   ⚠️  Too large! Compressing...")
                context = self._compress_context(context)
                estimated_tokens = self._estimate_tokens(context)
                print(f"   Compressed tokens: {estimated_tokens:,}")
            
            # Convert this node
            converted = self._convert_single_node(context)
            api_config["nodes"][f"__NODE{i}__"] = converted
            
            # Add connection
            api_config["connections"][f"edge-__NODE{i-1}__-__NODE{i}__"] = {
                "id": f"edge-__NODE{i-1}__-__NODE{i}__",
                "source": f"__NODE{i-1}__",
                "target": f"__NODE{i}__"
            }
        
        print(f"\n✅ Conversion complete! Generated {len(api_config['nodes'])} nodes")
        return api_config
    
    def _build_node_context(self, node: Dict, call_graph: Dict, api_config: Dict) -> Dict:
        """
        Build minimal context for converting a single node
        """
        # Get only metadata used in THIS node
        node_metadata = self._get_node_metadata(node, call_graph["metadata"])
        
        return {
            "node": {
                "signature": node.get("signature", {}),
                "source_code": compress_source_code(node.get("source_code", "")),
                "logic_annotations": node.get("logic_annotations", {})
            },
            "metadata": node_metadata,
            "previous_nodes": list(api_config["nodes"].values()),  # For context
            "conversion_hints": call_graph["metadata"].get("conversion_hints", {})
        }
    
    def _get_node_metadata(self, node: Dict, full_metadata: Dict) -> Dict:
        """
        Extract only metadata needed for this node
        """
        source_code = node.get("source_code", "")
        
        node_metadata = {
            "entities": {},
            "enums": {},
            "helper_methods": {},
            "database": {"dialect": full_metadata.get("database", {}).get("dialect", "mysql")}
        }
        
        # Only include entities referenced in this node
        for entity_name, entity_data in full_metadata.get("entities", {}).items():
            if entity_name in source_code:
                node_metadata["entities"][entity_name] = {
                    "table_name": entity_data["table_name"],
                    "fields": entity_data["fields"]
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
                    "source_code": compress_source_code(helper_data.get("source_code", ""))
                }
        
        return node_metadata
    
    def _estimate_tokens(self, context: Dict) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters)
        """
        json_str = json.dumps(context)
        return len(json_str) // 4
    
    def _compress_context(self, context: Dict) -> Dict:
        """
        Further compress context if still too large
        """
        # Remove logic annotations if present
        if "logic_annotations" in context.get("node", {}):
            context["node"]["logic_annotations"] = {
                "complexity_score": context["node"]["logic_annotations"].get("complexity_score", 0)
            }
        
        # Keep only essential conversion hints
        if "conversion_hints" in context:
            context["conversion_hints"] = {
                "critical_rules": context["conversion_hints"].get("critical_rules", [])
            }
        
        # Compress helper source code even more
        for helper_data in context.get("metadata", {}).get("helper_methods", {}).values():
            if "source_code" in helper_data:
                # Keep only method signature, remove implementation
                helper_data["source_code"] = helper_data.get("signature", "")
        
        return context
    
    def _convert_api_node(self, node: Dict, call_graph: Dict) -> Dict:
        """
        Convert the API node (simple, no LLM needed)
        """
        # API node conversion is straightforward
        return {
            "id": "__NODE1__",
            "type": "api",
            "position": {"x": 0, "y": 150},
            "data": {
                "label": "API",
                "isLastNode": False,
                "parameters": {
                    "apiName": call_graph["api_name"],
                    "httpMethod": "GET",  # Infer from method name
                    "path": f"/{call_graph['api_name']}",
                    # ... other API parameters
                }
            },
            "nodeName": call_graph["api_name"],
            "objectName": call_graph["api_name"].lower()
        }
    
    def _convert_single_node(self, context: Dict) -> Dict:
        """
        Convert a single node using LLM
        """
        # Call LLM with minimal context
        # This is where you'd call OpenAI/Claude/etc.
        pass
```

**Token Reduction:** 90-95% per LLM call!

---

## Strategy 6: Use Smaller Models for Simple Nodes

### **Problem:**
Using GPT-4 for every node is expensive

### **Solution:**
Use cheaper models for simple nodes

### **Implementation:**

```python
def select_model_for_node(node: Dict) -> str:
    """
    Select appropriate model based on node complexity
    """
    complexity = node.get("logic_annotations", {}).get("complexity_score", 0)
    
    if complexity < 5:
        return "gpt-3.5-turbo"  # Simple validation/formatting
    elif complexity < 15:
        return "gpt-4o-mini"  # Moderate complexity
    else:
        return "gpt-4o"  # Complex business logic
```

**Cost Reduction:** 80-90%

---

## Recommended Approach

### **Use Node-by-Node Conversion:**

```python
# In api_migration.py

async def perform_migration(
    migration_id: str,
    service_name: str,
    api_name: str,
    llm_model: str
):
    # ... build and enhance call graph ...
    
    # Convert node-by-node instead of all at once
    converter = NodeByNodeConverter(max_tokens_per_call=30000)
    api_config = converter.convert_call_graph(enhanced_graph)
    
    # Save result
    migration_jobs[migration_id].api_config = api_config
```

---

## Token Budget Example

### **Full Call Graph (BAD):**
```
System Prompt: 15,000 tokens
Call Graph:
  - 10 nodes × 5,000 tokens each = 50,000 tokens
  - Metadata = 20,000 tokens
  - Total = 85,000 tokens
  
TOTAL: 100,000 tokens ❌ (Too large!)
```

### **Node-by-Node (GOOD):**
```
Per Node:
  System Prompt: 5,000 tokens (simplified)
  Single Node: 3,000 tokens
  Node Metadata: 2,000 tokens
  Previous Context: 1,000 tokens
  
TOTAL per call: 11,000 tokens ✅ (Well within limits!)

For 10 nodes: 10 × 11,000 = 110,000 tokens total
But spread across 10 API calls (manageable!)
```

---

## Implementation Priority

1. ✅ **Implement Node-by-Node Conversion** (90% reduction)
2. ✅ **Add Source Code Compression** (20% additional)
3. ✅ **Use Node-Specific Metadata** (50% additional)
4. ⚠️ **Model Selection** (cost optimization)
5. ⚠️ **Caching** (reuse converted nodes)

---

## Next Steps

1. Create `NodeByNodeConverter` class
2. Update API endpoint to use it
3. Test with large call graphs
4. Monitor token usage
5. Optimize further if needed

Would you like me to implement the `NodeByNodeConverter` class?
