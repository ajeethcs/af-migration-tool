"""
Test script for the migration tool
Run this to verify the setup and test basic functionality
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.service_analyzer import ServiceAnalyzer
from core.call_graph_builder import CallGraphBuilder
import json

def test_service_discovery():
    """Test service discovery functionality"""
    print("\n" + "="*60)
    print("TEST 1: Service Discovery")
    print("="*60)
    
    try:
        analyzer = ServiceAnalyzer()
        services = analyzer.discover_services()
        
        print(f"\n✓ Found {len(services)} services:")
        for service in services[:5]:  # Show first 5
            print(f"  - {service.name} ({service.api_count} APIs)")
        
        if len(services) > 5:
            print(f"  ... and {len(services) - 5} more")
        
        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def test_api_listing():
    """Test API listing for a service"""
    print("\n" + "="*60)
    print("TEST 2: API Listing")
    print("="*60)
    
    try:
        analyzer = ServiceAnalyzer()
        
        # Try to get APIs for ClaimService
        service_name = "ClaimService"
        print(f"\nListing APIs for {service_name}...")
        
        apis = analyzer.get_service_apis(service_name)
        
        if apis:
            print(f"\n✓ Found {len(apis)} APIs:")
            for api in apis[:10]:  # Show first 10
                params = ", ".join([f"{p.type} {p.name}" for p in api.signature.parameters])
                print(f"  - {api.signature.return_type} {api.name}({params})")
            
            if len(apis) > 10:
                print(f"  ... and {len(apis) - 10} more")
        else:
            print(f"\n✗ No APIs found for {service_name}")
            return False
        
        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_call_graph_generation():
    """Test call graph generation"""
    print("\n" + "="*60)
    print("TEST 3: Call Graph Generation")
    print("="*60)
    
    try:
        # Try to build a call graph for a simple API
        service_name = "ClaimService"
        api_name = "viewEncounterBO"
        
        print(f"\nBuilding call graph for {service_name}.{api_name}...")
        
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(service_name, api_name)
        
        print(f"\n✓ Call graph generated successfully!")
        print(f"  - Entry point: {call_graph.entry_point}")
        print(f"  - Total nodes: {len(call_graph.nodes)}")
        print(f"  - Total edges: {len(call_graph.edges)}")
        
        print("\n  Node breakdown:")
        node_types = {}
        for node in call_graph.nodes:
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        for node_type, count in node_types.items():
            print(f"    - {node_type}: {count}")
        
        # Show first few nodes
        print("\n  Sample nodes:")
        for node in call_graph.nodes[:3]:
            print(f"    - {node.name} ({node.node_type}) in {node.class_name}")
        
        # Save to file for inspection
        output_file = Path(__file__).parent / "output" / "call_graphs" / "test_call_graph.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(call_graph.model_dump(), f, indent=2)
        
        print(f"\n  Call graph saved to: {output_file}")
        
        return True
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        print("  This is expected if the service/API doesn't exist")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MIGRATION TOOL TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Service Discovery", test_service_discovery()))
    results.append(("API Listing", test_api_listing()))
    results.append(("Call Graph Generation", test_call_graph_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The migration tool is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
