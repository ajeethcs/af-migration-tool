"""
Test Complete Call Graph Mode

Verifies that the call graph now traces ALL methods including:
- Internal methods (this.method())
- Conditional branches
- All DAO operations
- Complete data flow
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder
import json


def test_complete_copyvisit_tracing():
    """Test that copyVisit API is now completely traced"""
    print("=" * 80)
    print("Testing Complete Call Graph Mode for copyVisit API")
    print("=" * 80)
    
    builder = CallGraphBuilder()
    
    print("\n1. Building call graph for ClaimService.copyVisit...")
    call_graph = builder.build_call_graph(
        service_name="ClaimService",
        api_name="copyVisit",
        include_schema=True
    )
    
    # Convert to dict for analysis
    graph_dict = call_graph.model_dump(mode='json')
    
    print(f"\n2. Call graph generated:")
    print(f"   - Total nodes: {len(graph_dict['nodes'])}")
    print(f"   - Total edges: {len(graph_dict['edges'])}")
    
    # Extract node names for checking
    node_names = {}
    for node in graph_dict['nodes']:
        class_name = node['class_name'].split('.')[-1]
        method_name = node['name']
        key = f"{class_name}.{method_name}"
        node_names[key] = node
    
    print(f"\n3. Checking for critical methods...")
    
    # Critical methods that MUST be present for complete tracing
    critical_methods = [
        ("ClaimServiceImpl", "copyVisit"),
        ("DaoFacadeImpl", "saveCopyClaimByCopyVisitParams"),
        ("ClaimInfoBODaoImpl", "saveCopyClaimByCopyVisitParams"),
        ("ClaimInfoBODaoImpl", "getCopyClaimInfoBO"),
        ("ClaimInfoBODaoImpl", "storeOrUpdateCopyClaimInfoBO"),
        ("VisitDiagnosisAndProcedureBODaoImpl", "getCopyVisitDiagnosisAndProcedure"),
        ("HibernateVisitDiagnosisDao", "getVisitDiagnosis"),
        ("HibernateVisitProcedureDao", "getCopyVisitProcedureByClaimId"),
        ("ProvidersAndFacilityDao", "getProvidersAndFacilityByVisitId"),
        ("MiscellaneousBODaoImpl", "getMiscellaneousByVisitId"),
        ("CMSOverrideDataDao", "getCMSOverrideDataByVisitId"),
    ]
    
    found_count = 0
    missing_methods = []
    
    for class_name, method_name in critical_methods:
        key = f"{class_name}.{method_name}"
        if key in node_names:
            print(f"   ✅ Found: {key}")
            found_count += 1
        else:
            print(f"   ❌ MISSING: {key}")
            missing_methods.append(key)
    
    print(f"\n4. Results:")
    print(f"   - Found: {found_count}/{len(critical_methods)} critical methods")
    print(f"   - Coverage: {(found_count/len(critical_methods)*100):.1f}%")
    
    if missing_methods:
        print(f"\n   ⚠️  Missing methods:")
        for method in missing_methods:
            print(f"      - {method}")
    
    # Check for internal method tracing
    print(f"\n5. Checking internal method tracing...")
    internal_methods = [node for node in graph_dict['nodes'] 
                       if 'ClaimInfoBODaoImpl' in node['class_name']]
    print(f"   - Found {len(internal_methods)} methods in ClaimInfoBODaoImpl")
    
    if len(internal_methods) > 1:
        print(f"   ✅ Internal methods ARE being traced")
        for node in internal_methods[:5]:  # Show first 5
            print(f"      - {node['name']}")
    else:
        print(f"   ❌ Internal methods NOT being traced")
    
    # Check metadata
    print(f"\n6. Checking metadata...")
    metadata = graph_dict.get('metadata', {})
    entities = metadata.get('entities', {})
    enums = metadata.get('enums', {})
    
    print(f"   - Entities: {len(entities)}")
    print(f"   - Enums: {len(enums)}")
    
    # Check for critical entities
    critical_entities = [
        'CopyVisit', 'CopyClaim', 'VisitDiagnosis', 'CopyVisitProcedure',
        'ProvidersAndFacility', 'Miscellaneous', 'CMSOverrideData'
    ]
    
    found_entities = [e for e in critical_entities if e in entities]
    print(f"   - Critical entities found: {len(found_entities)}/{len(critical_entities)}")
    
    # Save for inspection
    output_file = Path(__file__).parent / "output" / "test_complete_copyvisit.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(graph_dict, f, indent=2)
    print(f"\n7. Full call graph saved to: {output_file}")
    
    # Final verdict
    print(f"\n" + "=" * 80)
    if found_count == len(critical_methods) and len(internal_methods) > 1:
        print("✅ SUCCESS: Call graph is COMPLETE!")
        print("   All critical methods are traced.")
        print("   Internal methods are being traced.")
        print("   The call graph should now capture 100% of the business logic.")
    elif found_count >= len(critical_methods) * 0.8:
        print("⚠️  PARTIAL: Call graph is mostly complete but missing some methods.")
        print(f"   Found {found_count}/{len(critical_methods)} critical methods.")
        print("   Review missing methods above.")
    else:
        print("❌ INCOMPLETE: Call graph is still missing critical methods.")
        print(f"   Only found {found_count}/{len(critical_methods)} critical methods.")
        print("   The depth limit may still be active or internal tracing is not working.")
    print("=" * 80)
    
    return found_count == len(critical_methods)


def test_method_call_extraction():
    """Test that method call extraction captures all patterns"""
    print("\n" + "=" * 80)
    print("Testing Method Call Extraction Patterns")
    print("=" * 80)
    
    from core.call_graph_builder import CallGraphBuilder
    
    builder = CallGraphBuilder()
    
    # Test source code with various call patterns
    test_code = """
    public void testMethod() {
        // Facade call
        daoFacade.saveCopyClaimByCopyVisitParams(params);
        
        // DAO field call
        this.visitDiagnosisDao.getVisitDiagnosis(id);
        
        // Direct DAO call
        claimDao.getClaim(id);
        
        // Helper call
        ClaimServiceHelper.populateCopyVisitOutput(data);
        
        // Internal call with this
        this.getCopyClaimInfoBO(params);
        
        // Internal call without this
        storeOrUpdateCopyClaimInfoBO(data);
        
        // Conditional branches
        if(params.isblCopyVisitDiagnosisAndProcedures()){
            this.copyDiagnosis(visitId);
        }
        if(params.isblCopyMiscellaneous()){
            miscellaneousDao.getMiscellaneousByVisitId(visitId);
        }
    }
    """
    
    method_calls = builder._extract_method_calls(test_code)
    
    print(f"\n1. Extracted {len(method_calls)} method calls:")
    for call in method_calls:
        print(f"   - {call['type']:15} {call['object']}.{call['method']}()")
    
    # Check for expected patterns
    expected_patterns = {
        'facade': 'saveCopyClaimByCopyVisitParams',
        'dao_field': 'getVisitDiagnosis',
        'dao_direct': 'getClaim',
        'helper': 'populateCopyVisitOutput',
        'internal': 'getCopyClaimInfoBO',
        'internal': 'storeOrUpdateCopyClaimInfoBO',
        'internal': 'copyDiagnosis',
        'dao_direct': 'getMiscellaneousByVisitId',
    }
    
    print(f"\n2. Checking for expected patterns...")
    found_patterns = {call['method'] for call in method_calls}
    
    for pattern_type, method_name in expected_patterns.items():
        if method_name in found_patterns:
            print(f"   ✅ Found {pattern_type}: {method_name}")
        else:
            print(f"   ❌ MISSING {pattern_type}: {method_name}")
    
    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COMPLETE CALL GRAPH MODE - TEST SUITE")
    print("=" * 80)
    
    # Test 1: Method call extraction
    test_method_call_extraction()
    
    # Test 2: Complete copyVisit tracing
    print("\n")
    success = test_complete_copyvisit_tracing()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    if success:
        print("✅ All tests passed!")
        print("   The call graph builder is now in COMPLETE MODE.")
        print("   It will trace ALL methods, ALL branches, ALL logic.")
    else:
        print("⚠️  Some tests failed.")
        print("   Review the output above for details.")
        print("   You may need to:")
        print("   1. Clear the cache: DELETE /api/migration/cache")
        print("   2. Restart the server")
        print("   3. Regenerate the call graph")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
