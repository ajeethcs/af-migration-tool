"""
Simple test to trace a single method and see what's extracted
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Enable debug output
import os
os.environ['DEBUG'] = '1'

from core.call_graph_builder import CallGraphBuilder
import json

print("="*60)
print("Simple Trace Test")
print("="*60)

try:
    service_name = "ClaimService"
    api_name = "getClaims"
    
    print(f"\nBuilding call graph for {service_name}.{api_name}...")
    
    builder = CallGraphBuilder()
    call_graph = builder.build_call_graph(service_name, api_name)
    
    print(f"\nCall graph built:")
    print(f"  Nodes: {len(call_graph.nodes)}")
    print(f"  Edges: {len(call_graph.edges)}")
    
    print("\nNodes:")
    for i, node in enumerate(call_graph.nodes, 1):
        print(f"\n{i}. {node.name} ({node.node_type})")
        print(f"   Class: {node.class_name}")
        print(f"   File: {Path(node.file_path).name}")
        print(f"   Line: {node.line_number}")
        print(f"   Dependencies: {len(node.dependencies)}")
        
        # Show first 5 lines of source
        if node.source_code:
            lines = node.source_code.split('\n')[:5]
            print(f"   Source (first 5 lines):")
            for line in lines:
                print(f"     {line[:80]}")
        else:
            print(f"   Source: [EMPTY]")
    
    print("\nEdges:")
    for edge in call_graph.edges:
        source_node = next((n for n in call_graph.nodes if n.id == edge.source), None)
        target_node = next((n for n in call_graph.nodes if n.id == edge.target), None)
        if source_node and target_node:
            print(f"  {source_node.name} --[{edge.call_type}]--> {target_node.name}")
    
    # Save for inspection
    output_file = Path(__file__).parent / "output" / "call_graphs" / "simple_trace.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(call_graph.model_dump(), f, indent=2)
    print(f"\nSaved to: {output_file}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
