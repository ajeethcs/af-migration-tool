"""
Test Metadata Filtering

Verifies that metadata is correctly filtered to only include
entities and enums used by the specific API.
"""
from core.metadata_filter import MetadataFilter, filter_metadata


def test_entity_detection_from_hql():
    """Test that entities are detected from HQL queries"""
    filterer = MetadataFilter()
    
    source_code = '''
    public List<MediumClaim> getClaims(int clinicId) {
        String query = "from MediumClaim mc where mc.C_ID = :clinicId";
        return session.createQuery(query).list();
    }
    '''
    
    all_entities = {
        'MediumClaim': {'table_name': 'CLAIM'},
        'Patient': {'table_name': 'PATIENT'},
        'Provider': {'table_name': 'PROVIDER'}
    }
    
    filterer._scan_for_entities(source_code, all_entities)
    
    assert 'MediumClaim' in filterer.used_entities
    assert 'Patient' not in filterer.used_entities
    assert 'Provider' not in filterer.used_entities


def test_entity_detection_from_new():
    """Test that entities are detected from 'new Entity()' patterns"""
    filterer = MetadataFilter()
    
    source_code = '''
    public void createClaim() {
        MediumClaim claim = new MediumClaim();
        claim.setClinicId(123);
    }
    '''
    
    all_entities = {
        'MediumClaim': {'table_name': 'CLAIM'},
        'Patient': {'table_name': 'PATIENT'}
    }
    
    filterer._scan_for_entities(source_code, all_entities)
    
    assert 'MediumClaim' in filterer.used_entities
    assert 'Patient' not in filterer.used_entities


def test_entity_detection_from_generics():
    """Test that entities are detected from generic types"""
    filterer = MetadataFilter()
    
    source_code = '''
    public List<MediumClaim> getAllClaims() {
        List<MediumClaim> claims = new ArrayList<>();
        return claims;
    }
    '''
    
    all_entities = {
        'MediumClaim': {'table_name': 'CLAIM'},
        'Patient': {'table_name': 'PATIENT'}
    }
    
    filterer._scan_for_entities(source_code, all_entities)
    
    assert 'MediumClaim' in filterer.used_entities


def test_enum_detection():
    """Test that enums are detected from source code"""
    filterer = MetadataFilter()
    
    source_code = '''
    public void checkStatus() {
        if (claim.getStatus() == Claim_ClaimStatus.CLAIMCREATED.getValue()) {
            // Process claim
        }
    }
    '''
    
    all_enums = {
        'Claim_ClaimStatus': {'CLAIMCREATED': 2},
        'PaymentStatus': {'PAID': 1}
    }
    
    filterer._scan_for_enums(source_code, all_enums)
    
    assert 'Claim_ClaimStatus' in filterer.used_enums
    assert 'PaymentStatus' not in filterer.used_enums


def test_filter_metadata_for_api():
    """Test complete metadata filtering for an API"""
    filterer = MetadataFilter()
    
    call_graph = {
        'api_name': 'getClaims',
        'nodes': [
            {
                'source_code': '''
                public List<MediumClaim> getClaims(int clinicId) {
                    String query = "from MediumClaim mc where mc.C_ID = :clinicId";
                    if (statusGroup[Claim_ClaimStatus.CLAIMCREATED.getValue()] == 1) {
                        query += " and mc.STATUS = :status";
                    }
                    return session.createQuery(query).list();
                }
                '''
            }
        ]
    }
    
    full_metadata = {
        'entities': {
            'MediumClaim': {
                'table_name': 'CLAIM',
                'fields': {'C_ID': {'column': 'CLINIC_ID'}}
            },
            'Patient': {
                'table_name': 'PATIENT',
                'fields': {'P_ID': {'column': 'PATIENT_ID'}}
            },
            'Provider': {
                'table_name': 'PROVIDER',
                'fields': {'PR_ID': {'column': 'PROVIDER_ID'}}
            }
        },
        'enums': {
            'Claim_ClaimStatus': {'CLAIMCREATED': 2, 'CLAIMFILED': 3},
            'PaymentStatus': {'PAID': 1, 'UNPAID': 2}
        },
        'database': {'dialect': 'mysql'}
    }
    
    filtered = filterer.filter_metadata_for_api(call_graph, full_metadata)
    
    # Should include only used entities
    assert 'MediumClaim' in filtered['entities']
    assert 'Patient' not in filtered['entities']
    assert 'Provider' not in filtered['entities']
    
    # Should include only used enums
    assert 'Claim_ClaimStatus' in filtered['enums']
    assert 'PaymentStatus' not in filtered['enums']
    
    # Should preserve database info
    assert filtered['database']['dialect'] == 'mysql'


def test_filter_metadata_with_multiple_entities():
    """Test filtering with multiple entities in joins"""
    filterer = MetadataFilter()
    
    call_graph = {
        'api_name': 'getClaimsWithVisits',
        'nodes': [
            {
                'source_code': '''
                public List<Object[]> getClaimsWithVisits() {
                    String query = "select mc, vd from MediumClaim mc " +
                                   "join VisitDetails vd on mc.V_ID = vd.iVisitId";
                    return session.createQuery(query).list();
                }
                '''
            }
        ]
    }
    
    full_metadata = {
        'entities': {
            'MediumClaim': {'table_name': 'CLAIM'},
            'VisitDetails': {'table_name': 'VISIT_DETAILS'},
            'Patient': {'table_name': 'PATIENT'}
        },
        'enums': {}
    }
    
    filtered = filterer.filter_metadata_for_api(call_graph, full_metadata)
    
    # Should include both entities used in join
    assert 'MediumClaim' in filtered['entities']
    assert 'VisitDetails' in filtered['entities']
    assert 'Patient' not in filtered['entities']


def test_skip_filtering_for_small_metadata():
    """Test that filtering is skipped for small metadata sets"""
    call_graph = {
        'api_name': 'simpleApi',
        'nodes': [{'source_code': 'from MediumClaim mc'}],
        'metadata': {
            'entities': {
                'MediumClaim': {'table_name': 'CLAIM'},
                'Patient': {'table_name': 'PATIENT'}
            },
            'enums': {
                'Status': {'ACTIVE': 1}
            }
        }
    }
    
    # Total entities + enums = 3 (< 20 threshold)
    result = filter_metadata(call_graph)
    
    # Should NOT filter (too small)
    assert len(result['metadata']['entities']) == 2
    assert len(result['metadata']['enums']) == 1


def test_filter_metadata_preserves_helpers():
    """Test that helper methods are always preserved"""
    filterer = MetadataFilter()
    
    call_graph = {
        'api_name': 'getClaims',
        'nodes': [{'source_code': 'from MediumClaim mc'}]
    }
    
    full_metadata = {
        'entities': {
            'MediumClaim': {'table_name': 'CLAIM'},
            'Patient': {'table_name': 'PATIENT'}
        },
        'enums': {},
        'helper_methods': {
            'getStatusString': {'signature': 'String getStatusString()'}
        },
        'conversion_hints': {
            'critical_rules': ['Use metadata.entities']
        }
    }
    
    filtered = filterer.filter_metadata_for_api(call_graph, full_metadata)
    
    # Helper methods should always be included
    assert 'helper_methods' in filtered
    assert 'getStatusString' in filtered['helper_methods']
    
    # Conversion hints should always be included
    assert 'conversion_hints' in filtered


def test_complex_hql_with_multiple_entities():
    """Test complex HQL with multiple entity references"""
    filterer = MetadataFilter()
    
    source_code = '''
    public List<Object[]> getComplexData() {
        String query = "select mc, p, pr from MediumClaim mc " +
                       "join Patient p on mc.P_ID = p.P_ID " +
                       "join Provider pr on mc.PR_ID = pr.PR_ID " +
                       "where mc.STATUS = :status";
        return session.createQuery(query).list();
    }
    '''
    
    all_entities = {
        'MediumClaim': {'table_name': 'CLAIM'},
        'Patient': {'table_name': 'PATIENT'},
        'Provider': {'table_name': 'PROVIDER'},
        'Insurance': {'table_name': 'INSURANCE'}
    }
    
    filterer._scan_for_entities(source_code, all_entities)
    
    # Should detect all three entities used in query
    assert 'MediumClaim' in filterer.used_entities
    assert 'Patient' in filterer.used_entities
    assert 'Provider' in filterer.used_entities
    
    # Should NOT include unused entity
    assert 'Insurance' not in filterer.used_entities


def test_percentage_calculation():
    """Test percentage calculation helper"""
    filterer = MetadataFilter()
    
    assert filterer._percentage(50, 100) == 50
    assert filterer._percentage(1, 100) == 1
    assert filterer._percentage(0, 100) == 0
    assert filterer._percentage(10, 0) == 0  # Edge case: division by zero


def test_real_world_scenario():
    """Test a realistic scenario with many entities"""
    filterer = MetadataFilter()
    
    # Simulate a real API that uses only 3 entities out of 150
    call_graph = {
        'api_name': 'getClaims',
        'nodes': [
            {
                'source_code': '''
                public GetClaimsOutput getClaims(int clinicId, byte[] statusGroup) {
                    String query = "from MediumClaim mc where mc.C_ID = :clinicId";
                    
                    if (statusGroup[Claim_ClaimStatus.CLAIMCREATED.getValue()] == 1) {
                        query += " and mc.STATUS = :status";
                    }
                    
                    List<MediumClaim> claims = session.createQuery(query).list();
                    return new GetClaimsOutput(claims);
                }
                '''
            }
        ]
    }
    
    # Simulate 150 entities (only 1 used)
    all_entities = {f'Entity{i}': {'table_name': f'TABLE_{i}'} for i in range(150)}
    all_entities['MediumClaim'] = {'table_name': 'CLAIM'}
    
    # Simulate 100 enums (only 1 used)
    all_enums = {f'Enum{i}': {f'VALUE{i}': i} for i in range(100)}
    all_enums['Claim_ClaimStatus'] = {'CLAIMCREATED': 2}
    
    full_metadata = {
        'entities': all_entities,
        'enums': all_enums,
        'database': {'dialect': 'mysql'}
    }
    
    filtered = filterer.filter_metadata_for_api(call_graph, full_metadata)
    
    # Should drastically reduce metadata
    assert len(filtered['entities']) == 1  # Only MediumClaim
    assert len(filtered['enums']) == 1     # Only Claim_ClaimStatus
    
    # Calculate savings
    original_count = len(all_entities) + len(all_enums)  # 250
    filtered_count = len(filtered['entities']) + len(filtered['enums'])  # 2
    savings_percent = ((original_count - filtered_count) / original_count) * 100
    
    assert savings_percent > 99  # Should save >99% of metadata


if __name__ == "__main__":
    # Run tests
    print("Running metadata filtering tests...\n")
    
    test_entity_detection_from_hql()
    print("✓ Entity detection from HQL")
    
    test_entity_detection_from_new()
    print("✓ Entity detection from 'new' keyword")
    
    test_entity_detection_from_generics()
    print("✓ Entity detection from generics")
    
    test_enum_detection()
    print("✓ Enum detection")
    
    test_filter_metadata_for_api()
    print("✓ Complete metadata filtering")
    
    test_filter_metadata_with_multiple_entities()
    print("✓ Multiple entity filtering")
    
    test_skip_filtering_for_small_metadata()
    print("✓ Skip filtering for small metadata")
    
    test_filter_metadata_preserves_helpers()
    print("✓ Helper methods preservation")
    
    test_complex_hql_with_multiple_entities()
    print("✓ Complex HQL parsing")
    
    test_percentage_calculation()
    print("✓ Percentage calculation")
    
    test_real_world_scenario()
    print("✓ Real-world scenario (99% reduction)")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✅")
    print("="*60)
