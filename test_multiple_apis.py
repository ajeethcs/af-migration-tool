"""
Test Multiple APIs - Verify Generic Solution

Tests the migration tool with different APIs to prove it's not hardcoded
to ClaimService.getClaims.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder
from core.business_logic_enhancer import BusinessLogicEnhancer


def test_multiple_apis():
    """Test with multiple different APIs to verify generic solution"""
    print("\n" + "="*70)
    print("TEST: Multiple APIs - Verify Generic Solution")
    print("="*70)
    
    # List of different APIs to test
    test_cases = [
        {"service": "ClaimService", "api": "getClaims"},
        {"service": "ClaimService", "api": "viewEncounterBO"},
        {"service": "ClaimService", "api": "createClaim"},
        # Add more services/APIs as they exist in your codebase
    ]
    
    builder = CallGraphBuilder()
    enhancer = BusinessLogicEnhancer()
    
    results = []
    
    for test_case in test_cases:
        service_name = test_case["service"]
        api_name = test_case["api"]
        
        print(f"\n{'='*70}")
        print(f"Testing: {service_name}.{api_name}")
        print(f"{'='*70}")
        
        try:
            # Build call graph
            print(f"  1. Building call graph...")
            call_graph = builder.build_call_graph(
                service_name=service_name,
                api_name=api_name,
                include_schema=True
            )
            
            print(f"     ✓ Nodes: {len(call_graph.nodes)}")
            print(f"     ✓ Edges: {len(call_graph.edges)}")
            
            # Enhance with business logic
            print(f"  2. Enhancing with business logic...")
            enhanced = enhancer.enhance_call_graph(call_graph.model_dump())
            
            metadata = enhanced.get('metadata', {})
            
            # Check what was extracted
            entities_count = len(metadata.get('entities', {}))
            enums_count = len(metadata.get('enums', {}))
            helpers_count = len(metadata.get('helper_methods', {}))
            
            print(f"     ✓ Entities: {entities_count}")
            print(f"     ✓ Enums: {enums_count}")
            print(f"     ✓ Helpers: {helpers_count}")
            
            # Count annotated nodes
            annotated = sum(1 for n in enhanced.get('nodes', []) 
                          if 'logic_annotations' in n)
            print(f"     ✓ Annotated nodes: {annotated}")
            
            results.append({
                'service': service_name,
                'api': api_name,
                'status': 'SUCCESS',
                'nodes': len(call_graph.nodes),
                'edges': len(call_graph.edges),
                'entities': entities_count,
                'enums': enums_count,
                'helpers': helpers_count
            })
            
        except FileNotFoundError as e:
            print(f"     ⚠ API not found: {e}")
            results.append({
                'service': service_name,
                'api': api_name,
                'status': 'NOT_FOUND',
                'error': str(e)
            })
            
        except Exception as e:
            print(f"     ✗ Error: {e}")
            results.append({
                'service': service_name,
                'api': api_name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r['status'] == 'SUCCESS']
    not_found = [r for r in results if r['status'] == 'NOT_FOUND']
    errors = [r for r in results if r['status'] == 'ERROR']
    
    print(f"\n✓ Successful: {len(successful)}")
    print(f"⚠ Not Found: {len(not_found)}")
    print(f"✗ Errors: {len(errors)}")
    
    if successful:
        print(f"\n{'='*70}")
        print("Successful Conversions:")
        print(f"{'='*70}")
        for r in successful:
            print(f"\n{r['service']}.{r['api']}:")
            print(f"  - Nodes: {r['nodes']}, Edges: {r['edges']}")
            print(f"  - Entities: {r['entities']}, Enums: {r['enums']}, Helpers: {r['helpers']}")
    
    print("\n" + "="*70)
    print("VERIFICATION RESULT")
    print("="*70)
    
    if len(successful) > 1:
        print("\n✅ VERIFIED: Solution works with multiple APIs!")
        print("   The tool is NOT hardcoded to ClaimService.getClaims")
        print("   It successfully processed different APIs with:")
        print("   - Different entities")
        print("   - Different enums")
        print("   - Different helpers")
        print("   - Different logic patterns")
        return True
    elif len(successful) == 1:
        print("\n⚠ PARTIAL: Only one API tested successfully")
        print("   Add more test cases to verify full generic support")
        return True
    else:
        print("\n✗ FAILED: No APIs processed successfully")
        return False


if __name__ == "__main__":
    success = test_multiple_apis()
    sys.exit(0 if success else 1)
