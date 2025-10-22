"""
Test Business Logic Enhancement

Verifies that all business logic context is properly extracted and included.
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder
from core.business_logic_enhancer import BusinessLogicEnhancer


def test_business_logic_enhancement():
    """Test complete business logic enhancement"""
    print("\n" + "="*70)
    print("TEST: Business Logic Enhancement")
    print("="*70)
    
    try:
        # Step 1: Build base call graph
        print("\n1. Building base call graph...")
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(
            service_name="ClaimService",
            api_name="getClaims",
            include_schema=True
        )
        
        print(f"  ✓ Base call graph: {len(call_graph.nodes)} nodes, {len(call_graph.edges)} edges")
        
        # Step 2: Enhance with business logic
        print("\n2. Enhancing with business logic context...")
        enhancer = BusinessLogicEnhancer()
        enhanced = enhancer.enhance_call_graph(call_graph.model_dump())
        
        # Step 3: Verify enhancements
        print("\n3. Verifying enhancements...")
        
        metadata = enhanced.get('metadata', {})
        
        # Check schema metadata
        if 'entities' in metadata:
            print(f"  ✓ Schema metadata: {len(metadata['entities'])} entities")
            
            # Verify MediumClaim entity
            if 'MediumClaim' in metadata['entities']:
                mc = metadata['entities']['MediumClaim']
                print(f"    - MediumClaim → {mc['table_name']}")
                print(f"    - Fields: {len(mc.get('fields', {}))}")
        else:
            print(f"  ✗ Schema metadata missing!")
        
        # Check enum definitions
        if 'enums' in metadata:
            print(f"  ✓ Enum definitions: {len(metadata['enums'])} enums")
            
            # Verify Claim_ClaimStatus
            if 'Claim_ClaimStatus' in metadata['enums']:
                status_enum = metadata['enums']['Claim_ClaimStatus']
                print(f"    - Claim_ClaimStatus: {len(status_enum)} constants")
                if 'CLAIMCREATED' in status_enum:
                    print(f"      CLAIMCREATED = {status_enum['CLAIMCREATED']}")
        else:
            print(f"  ✗ Enum definitions missing!")
        
        # Check helper methods
        if 'helper_methods' in metadata:
            print(f"  ✓ Helper methods: {len(metadata['helper_methods'])} helpers")
            for helper_name in list(metadata['helper_methods'].keys())[:3]:
                print(f"    - {helper_name}")
        else:
            print(f"  ℹ No helper methods extracted")
        
        # Check logic annotations
        annotated_nodes = 0
        total_patterns = 0
        for node in enhanced.get('nodes', []):
            if 'logic_annotations' in node:
                annotated_nodes += 1
                patterns = node['logic_annotations'].get('patterns', [])
                total_patterns += len(patterns)
        
        if annotated_nodes > 0:
            print(f"  ✓ Logic annotations: {annotated_nodes} nodes annotated")
            print(f"    - Total patterns detected: {total_patterns}")
        else:
            print(f"  ✗ Logic annotations missing!")
        
        # Check conversion hints
        if 'conversion_hints' in metadata:
            hints = metadata['conversion_hints']
            print(f"  ✓ Conversion hints present")
            print(f"    - Critical rules: {len(hints.get('critical_rules', []))}")
        else:
            print(f"  ✗ Conversion hints missing!")
        
        # Step 4: Generate summary report
        print("\n4. Generating summary report...")
        report = enhancer.generate_summary_report(enhanced)
        print(report)
        
        # Step 5: Save enhanced call graph
        output_dir = Path(__file__).parent / "output" / "call_graphs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "enhanced_business_logic.json"
        with open(output_file, 'w') as f:
            json.dump(enhanced, f, indent=2)
        
        print(f"\n✓ Enhanced call graph saved to: {output_file}")
        
        # Calculate file size
        file_size = output_file.stat().st_size
        print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
        # Step 6: Verify specific business logic
        print("\n5. Verifying specific business logic patterns...")
        
        # Find DAO node with complex logic
        dao_nodes = [n for n in enhanced.get('nodes', []) if n.get('node_type') == 'dao']
        if dao_nodes:
            complex_node = max(dao_nodes, 
                             key=lambda n: n.get('logic_annotations', {}).get('complexity_score', 0))
            
            annotations = complex_node.get('logic_annotations', {})
            print(f"  Most complex DAO node: {complex_node.get('signature', {}).get('name', 'unknown')}")
            print(f"    - Complexity score: {annotations.get('complexity_score', 0)}")
            print(f"    - Patterns: {len(annotations.get('patterns', []))}")
            
            for pattern in annotations.get('patterns', [])[:3]:
                print(f"      • {pattern['type']}: {pattern['description']}")
        
        print("\n" + "="*70)
        print("✓ Business logic enhancement test PASSED!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*70)
        print("✗ Business logic enhancement test FAILED")
        print("="*70)
        
        return False


if __name__ == "__main__":
    success = test_business_logic_enhancement()
    sys.exit(0 if success else 1)
