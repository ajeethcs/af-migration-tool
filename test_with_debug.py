"""
Test with debug output enabled
"""
import sys
import os
from pathlib import Path

# Enable debug BEFORE importing
os.environ['DEBUG_CALL_GRAPH'] = '1'

sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder

print("="*60)
print("Test with Debug Output")
print("="*60)

try:
    service_name = "ClaimService"
    api_name = "getClaims"
    
    print(f"\nBuilding call graph for {service_name}.{api_name}...")
    print("Debug output enabled - will show pattern matches\n")
    
    builder = CallGraphBuilder()
    call_graph = builder.build_call_graph(service_name, api_name)
    
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"  Total nodes: {len(call_graph.nodes)}")
    print(f"  Total edges: {len(call_graph.edges)}")
    
    # Check for DAO nodes
    dao_nodes = [n for n in call_graph.nodes if n.node_type == "dao"]
    print(f"  DAO nodes: {len(dao_nodes)}")
    
    if dao_nodes:
        print("\n[SUCCESS] DAO nodes found!")
        for node in dao_nodes:
            print(f"  - {node.name} in {node.class_name}")
    else:
        print("\n[ISSUE] No DAO nodes found")
        print("\nFacade node details:")
        facade_nodes = [n for n in call_graph.nodes if n.node_type == "facade"]
        for node in facade_nodes:
            print(f"\n  Name: {node.name}")
            print(f"  Dependencies: {len(node.dependencies)}")
            print(f"  Source code length: {len(node.source_code)} chars")
            print(f"  Source preview:")
            for line in node.source_code.split('\n')[:10]:
                print(f"    {line}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
