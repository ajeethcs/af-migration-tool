"""
Test script to verify DAO-level tracing
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder
import json

def test_dao_tracing():
    """Test that call graph traces into DAO implementations"""
    print("\n" + "="*60)
    print("TEST: DAO-Level Tracing")
    print("="*60)
    
    try:
        # Test with an API that calls DAO methods
        service_name = "ClaimService"
        api_name = "getClaims"  # or another API that goes through facade to DAO
        
        print(f"\nBuilding call graph for {service_name}.{api_name}...")
        print("This should trace through:")
        print("  1. ServiceImpl method")
        print("  2. DaoFacade method")
        print("  3. DAO implementation method (e.g., MediumClaimBODaoImpl)")
        print("  4. Any methods called within the DAO")
        
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(service_name, api_name)
        
        print(f"\n✓ Call graph generated successfully!")
        print(f"  - Total nodes: {len(call_graph.nodes)}")
        print(f"  - Total edges: {len(call_graph.edges)}")
        
        # Analyze node types
        node_types = {}
        for node in call_graph.nodes:
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        print("\n  Node breakdown:")
        for node_type, count in node_types.items():
            print(f"    - {node_type}: {count}")
        
        # Check if we have DAO nodes
        dao_nodes = [node for node in call_graph.nodes if node.node_type == "dao"]
        
        if dao_nodes:
            print(f"\n✓ SUCCESS: Found {len(dao_nodes)} DAO node(s)!")
            print("\n  DAO nodes found:")
            for node in dao_nodes:
                print(f"    - {node.name} in {node.class_name}")
                print(f"      File: {node.file_path}")
                print(f"      Dependencies: {len(node.dependencies)} method(s)")
        else:
            print("\n⚠️  WARNING: No DAO nodes found in the call graph")
            print("  This might mean:")
            print("  - The API doesn't call DAO methods directly")
            print("  - The DAO pattern matching needs adjustment")
        
        # Show the complete call chain
        print("\n  Complete call chain:")
        visited = set()
        
        def print_chain(node_id, depth=0):
            if node_id in visited or depth > 10:
                return
            visited.add(node_id)
            
            node = next((n for n in call_graph.nodes if n.id == node_id), None)
            if node:
                indent = "  " * depth
                print(f"{indent}└─ {node.name} ({node.node_type})")
                for dep_id in node.dependencies:
                    print_chain(dep_id, depth + 1)
        
        print_chain(call_graph.entry_point)
        
        # Save to file
        output_file = Path(__file__).parent / "output" / "call_graphs" / "test_dao_tracing.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(call_graph.model_dump(), f, indent=2)
        
        print(f"\n  Call graph saved to: {output_file}")
        
        return len(dao_nodes) > 0
        
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        print("  Make sure the service and API names are correct")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dao_tracing()
    
    if success:
        print("\n" + "="*60)
        print("✓ DAO tracing is working correctly!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("⚠️  DAO tracing needs verification")
        print("="*60)
