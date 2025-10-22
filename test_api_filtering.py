"""
Test API Filtering

Quick test to verify that the FastAPI endpoint is now filtering metadata.
"""
import requests
import json
import time


def test_api_filtering():
    """Test that the API returns filtered metadata"""
    
    base_url = "http://localhost:8000"
    
    print("="*70)
    print("TESTING API METADATA FILTERING")
    print("="*70)
    
    # Step 1: Start migration
    print("\n1. Starting migration...")
    response = requests.post(
        f"{base_url}/api/migration/start",
        json={
            "service_name": "ClaimService",
            "api_name": "getClaims"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to start migration: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    migration_id = data["migration_id"]
    print(f"✓ Migration started: {migration_id}")
    
    # Step 2: Wait for completion
    print("\n2. Waiting for completion...")
    max_attempts = 30
    for i in range(max_attempts):
        time.sleep(2)
        
        status_response = requests.get(f"{base_url}/api/migration/status/{migration_id}")
        status_data = status_response.json()
        
        print(f"   Status: {status_data['status']} - {status_data['message']}")
        
        if status_data['status'] == 'completed':
            print("✓ Migration completed!")
            break
        elif status_data['status'] == 'failed':
            print(f"❌ Migration failed: {status_data['message']}")
            return False
    else:
        print("❌ Migration timed out")
        return False
    
    # Step 3: Get call graph
    print("\n3. Fetching call graph...")
    graph_response = requests.get(f"{base_url}/api/migration/call-graph/{migration_id}")
    
    if graph_response.status_code != 200:
        print(f"❌ Failed to get call graph: {graph_response.status_code}")
        return False
    
    call_graph = graph_response.json()
    print("✓ Call graph retrieved")
    
    # Step 4: Check metadata
    print("\n4. Analyzing metadata...")
    
    if 'metadata' not in call_graph:
        print("❌ No metadata in call graph!")
        return False
    
    metadata = call_graph['metadata']
    
    # Count entities and enums
    entity_count = len(metadata.get('entities', {}))
    enum_count = len(metadata.get('enums', {}))
    helper_count = len(metadata.get('helper_methods', {}))
    
    print(f"\n📊 Metadata Statistics:")
    print(f"   Entities: {entity_count}")
    print(f"   Enums: {enum_count}")
    print(f"   Helpers: {helper_count}")
    
    # List entities
    if entity_count > 0:
        print(f"\n   Entity names: {', '.join(metadata['entities'].keys())}")
    
    # List enums
    if enum_count > 0:
        print(f"   Enum names: {', '.join(metadata['enums'].keys())}")
    
    # Step 5: Verify filtering
    print("\n5. Verifying filtering...")
    
    # Expected: Small number of entities/enums (should be < 10 each)
    if entity_count > 20:
        print(f"⚠️  WARNING: Too many entities ({entity_count})")
        print("   Filtering may not be working!")
        print("   Expected: < 10 entities for a typical API")
        return False
    
    if enum_count > 20:
        print(f"⚠️  WARNING: Too many enums ({enum_count})")
        print("   Filtering may not be working!")
        print("   Expected: < 10 enums for a typical API")
        return False
    
    print(f"✓ Filtering is working! Only {entity_count} entities and {enum_count} enums")
    
    # Step 6: Check for specific entities (should be only what's used)
    print("\n6. Checking entity relevance...")
    
    # For getClaims, we expect entities like MediumClaim, possibly VisitDetails
    expected_entities = ['MediumClaim', 'VisitDetails', 'ClaimStatus']
    found_relevant = False
    
    for entity in metadata.get('entities', {}).keys():
        if entity in expected_entities:
            found_relevant = True
            print(f"   ✓ Found relevant entity: {entity}")
    
    if not found_relevant:
        print("   ⚠️  No expected entities found")
    
    # Step 7: Save for inspection
    print("\n7. Saving call graph for inspection...")
    output_file = "test_filtered_call_graph.json"
    with open(output_file, 'w') as f:
        json.dump(call_graph, f, indent=2)
    print(f"✓ Saved to: {output_file}")
    
    print("\n" + "="*70)
    print("TEST COMPLETED SUCCESSFULLY! ✅")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Entities: {entity_count} (filtered)")
    print(f"  - Enums: {enum_count} (filtered)")
    print(f"  - Helpers: {helper_count}")
    print(f"  - Filtering: {'✓ WORKING' if entity_count < 20 else '❌ NOT WORKING'}")
    print("="*70)
    
    return True


def test_unfiltered_comparison():
    """
    Compare filtered vs unfiltered metadata sizes
    (This requires temporarily disabling filtering)
    """
    print("\n" + "="*70)
    print("FILTERED VS UNFILTERED COMPARISON")
    print("="*70)
    print("\nTo see the difference:")
    print("1. Temporarily set filter_metadata=False in api_migration.py")
    print("2. Restart the server")
    print("3. Run this test again")
    print("4. Compare entity/enum counts")
    print("\nExpected:")
    print("  - Unfiltered: ~156 entities, ~98 enums")
    print("  - Filtered: ~3 entities, ~2 enums")
    print("  - Reduction: ~97%")
    print("="*70)


if __name__ == "__main__":
    print("\n🧪 Testing API Metadata Filtering\n")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            print("Please start the server with: python main.py")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("Please start the server with: python main.py")
        exit(1)
    
    print("✓ Server is running\n")
    
    # Run the test
    try:
        success = test_api_filtering()
        
        if success:
            print("\n✅ All tests passed!")
            print("\nThe API is now returning filtered metadata!")
        else:
            print("\n❌ Tests failed!")
            print("\nPlease check the server logs for errors.")
        
        # Show comparison info
        test_unfiltered_comparison()
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
