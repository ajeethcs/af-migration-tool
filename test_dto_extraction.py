"""
Test DTO extraction functionality
"""
import json
from core.call_graph_builder import CallGraphBuilder

def test_dto_extraction():
    """Test that DTO definitions are included in call graph metadata"""
    
    print("="*70)
    print("Testing DTO Extraction in Call Graph")
    print("="*70)
    
    # Build call graph for viewPatientByPatientId API
    builder = CallGraphBuilder()
    call_graph = builder.build_call_graph(
        service_name="ClaimService",
        api_name="getClaims",
        include_schema=True
    )
    
    # Convert to dict (mode='json' ensures all types are JSON serializable)
    graph_dict = call_graph.model_dump(mode='json')
    
    # Check metadata
    print("\n1. Checking metadata keys...")
    metadata = graph_dict.get('metadata', {})
    print(f"   Metadata keys: {list(metadata.keys())}")
    
    # Check if DTOs are present
    print("\n2. Checking DTO definitions...")
    dtos = metadata.get('dtos', {})
    print(f"   Total DTOs extracted: {len(dtos)}")
    
    if dtos:
        print("\n3. DTO Classes found:")
        for dto_name in sorted(dtos.keys()):
            dto = dtos[dto_name]
            field_count = len(dto.get('fields', {}))
            print(f"   - {dto_name}: {field_count} fields")
        
        # Show detailed info for ViewPatientOutput
        if 'ViewPatientOutput' in dtos:
            print("\n4. ViewPatientOutput Details:")
            vpo = dtos['ViewPatientOutput']
            print(f"   Package: {vpo.get('package')}")
            print(f"   Fully Qualified Name: {vpo.get('fully_qualified_name')}")
            print(f"   Extends: {vpo.get('extends')}")
            print(f"   Fields ({len(vpo.get('fields', {}))} total):")
            for field_name, field_info in list(vpo.get('fields', {}).items())[:10]:
                print(f"      - {field_name}: {field_info.get('type')}")
            if len(vpo.get('fields', {})) > 10:
                print(f"      ... and {len(vpo.get('fields', {})) - 10} more fields")
        else:
            print("\n   ⚠ ViewPatientOutput not found in DTOs!")
            print(f"   Available DTOs: {list(dtos.keys())}")
    else:
        print("   ⚠ No DTOs extracted!")
    
    # Save to file for inspection
    output_file = "output/call_graphs/test_dto_extraction.json"
    with open(output_file, 'w') as f:
        json.dump(graph_dict, f, indent=2)
    
    print(f"\n5. Full call graph saved to: {output_file}")
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)

if __name__ == "__main__":
    test_dto_extraction()
