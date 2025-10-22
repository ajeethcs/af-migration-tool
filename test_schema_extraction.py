"""
Test script to verify schema extraction from Hibernate mappings
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder

def test_schema_extraction():
    """Test schema extraction with call graph"""
    print("\n" + "="*60)
    print("TEST: Schema Extraction with Call Graph")
    print("="*60)
    
    try:
        service_name = "ClaimService"
        api_name = "getClaims"
        
        print(f"\nBuilding call graph for {service_name}.{api_name}...")
        print("With schema metadata extraction enabled")
        
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(
            service_name=service_name,
            api_name=api_name,
            include_schema=True  # Enable schema extraction
        )
        
        print(f"\n✓ Call graph generated successfully!")
        print(f"  - Total nodes: {len(call_graph.nodes)}")
        print(f"  - Total edges: {len(call_graph.edges)}")
        
        # Check if metadata was added
        if "entities" in call_graph.metadata:
            print(f"\n✓ Schema metadata extracted!")
            print(f"  - Entities: {len(call_graph.metadata['entities'])}")
            
            # Show sample entity mapping
            if "MediumClaim" in call_graph.metadata["entities"]:
                print(f"\n  Sample: MediumClaim entity mapping")
                medium_claim = call_graph.metadata["entities"]["MediumClaim"]
                print(f"    Table: {medium_claim['table_name']}")
                print(f"    Primary Key: {medium_claim['primary_key']}")
                print(f"    Fields: {len(medium_claim['fields'])}")
                
                # Show first 5 field mappings
                print(f"\n    Sample field mappings:")
                for i, (field_name, field_info) in enumerate(list(medium_claim['fields'].items())[:5]):
                    print(f"      {field_name} → {field_info['column']}")
        
        if "enums" in call_graph.metadata:
            print(f"\n✓ Enum definitions extracted!")
            print(f"  - Enums: {len(call_graph.metadata['enums'])}")
            
            # Show sample enum
            if call_graph.metadata["enums"]:
                sample_enum = list(call_graph.metadata["enums"].items())[0]
                print(f"\n  Sample: {sample_enum[0]}")
                for const_name, const_value in list(sample_enum[1].items())[:5]:
                    print(f"    {const_name} = {const_value}")
        
        # Save enhanced call graph
        output_file = Path(__file__).parent / "output" / "call_graphs" / "with_schema.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(call_graph.model_dump(), f, indent=2)
        
        print(f"\n✓ Enhanced call graph saved to: {output_file}")
        
        # Calculate size difference
        file_size = output_file.stat().st_size
        print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
        print("\n" + "="*60)
        print("✓ Schema extraction test PASSED!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*60)
        print("✗ Schema extraction test FAILED")
        print("="*60)
        
        return False

if __name__ == "__main__":
    success = test_schema_extraction()
    sys.exit(0 if success else 1)
