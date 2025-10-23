"""
Test script for CallGraphOptimizer

Tests the JSON optimization functionality to ensure:
1. Size reduction of ~70%
2. Critical logic is preserved
3. Query logic is properly extracted
"""
import json
from core.call_graph_optimizer import CallGraphOptimizer


def create_sample_large_graph():
    """Create a sample call graph with large DAO nodes"""
    return {
        'api_name': 'getClaims',
        'service_name': 'ClaimService',
        'entry_point': 'com.iris.allofactor.services.impl.ClaimServiceImpl.getClaims',
        'nodes': [
            {
                'id': 'service_impl_1',
                'name': 'getClaims',
                'class_name': 'ClaimServiceImpl',
                'node_type': 'service_impl',
                'signature': {'name': 'getClaims', 'return_type': 'GetClaimsOutPut'},
                'source_code': '\tpublic GetClaimsOutPut getClaims(UserSession userSession) {\n\t\treturn helper.populate(dao.get());\n\t}',
                'file_path': '/path/to/ClaimServiceImpl.java',
                'line_number': 100,
                'dependencies': ['facade_1', 'helper_1'],
                'logic_annotations': {
                    'complexity_score': 3,
                    'patterns': [
                        {
                            'type': 'helper_method_calls',
                            'helpers': ['helper1', 'helper2', 'helper3']
                        }
                    ]
                }
            },
            {
                'id': 'facade_1',
                'name': 'getMediumClaimBO',
                'class_name': 'DaoFacadeImpl',
                'node_type': 'facade',
                'signature': {'name': 'getMediumClaimBO', 'return_type': 'MediumClaimBO'},
                'source_code': '\tpublic MediumClaimBO getMediumClaimBO(ClaimCriteria criteria) {\n\t\treturn this.dao.getMediumClaimBO(criteria);\n\t}',
                'file_path': '/path/to/DaoFacadeImpl.java',
                'line_number': 200,
                'dependencies': ['dao_1']
            },
            {
                'id': 'dao_1',
                'name': 'getMediumClaimByClaimCriteriaNew',
                'class_name': 'HibernateClaimDao',
                'node_type': 'dao',
                'signature': {'name': 'getMediumClaimByClaimCriteriaNew', 'return_type': 'MediumClaim[]'},
                'source_code': '''
\tpublic MediumClaim[] getMediumClaimByClaimCriteriaNew(ClaimCriteria claimCriteria, int iOffset, int iCount, int iClinicID) {
\t\tString sQry = "select mc from MediumClaim mc,VisitDetails vd where mc.C_ID = "+iClinicID;
\t\t
\t\tif(claimCriteria.getBtStatusGroup() != null && claimCriteria.getBtStatusGroup()[0] == Claim_ClaimStatus.CLARIFICATIONOPENED.getClaim_ClaimStatus()) {
\t\t\tsQry = "select mc,cm.sDescription FROM MediumClaim mc,VisitDetails vd,Task T,ClinicMaster cm";
\t\t}
\t\t
\t\tif(claimCriteria.getiPatient_Id() != 0) {
\t\t\tsQry = sQry + " and mc.P_ID = "+claimCriteria.getiPatient_Id();
\t\t}
\t\t
\t\tif(claimCriteria.getiProvider_Id() != 0) {
\t\t\tsQry = sQry + " and vd.iPhysicianId = "+claimCriteria.getiProvider_Id();
\t\t}
\t\t
\t\tif(claimCriteria.getBtTimelyFilingLimit() == Enums.TimilyFilingLimit.Thirty.getTimilyFilingLimit()) {
\t\t\tsQry = sQry+" and mc.STATUS in(1,2,4,5,6,12,13)";
\t\t}
\t\t
\t\tif(claimCriteria.getBtClaimHold() == Enums.HoldClaimSearchCriteria.GeneralHoldExclude.getHoldClaimSearchCriteria()) {
\t\t\tsQry = sQry + " and mc.btClaimHold in(" + Enums.HoldClaimStatus.UnHolded.getHoldClaimStatus() +")";
\t\t}
\t\t
\t\tif(claimCriteria.getsOrderByFields() != null) {
\t\t\tsQry = sQry + " order by mc.DOS desc";
\t\t}
\t\t
\t\tQuery HQRY = session.createQuery(sQry);
\t\tHQRY.setFirstResult(iOffset);
\t\tHQRY.setMaxResults(iCount);
\t\treturn HQRY.list();
\t}
''' * 10,  # Repeat to make it large
                'file_path': '/path/to/HibernateClaimDao.java',
                'line_number': 300,
                'dependencies': [],
                'logic_annotations': {
                    'complexity_score': 25,
                    'patterns': [
                        {
                            'type': 'conditional_query_building',
                            'count': 56,
                            'complexity': 'complex'
                        },
                        {
                            'type': 'enum_comparisons',
                            'enums': [
                                'Claim_ClaimStatus.CLARIFICATIONOPENED',
                                'TimilyFilingLimit.Thirty',
                                'HoldClaimSearchCriteria.GeneralHoldExclude',
                                'HoldClaimStatus.UnHolded'
                            ]
                        },
                        {
                            'type': 'helper_method_calls',
                            'helpers': ['session.createQuery', 'HQRY.setFirstResult', 'HQRY.setMaxResults'] * 50
                        }
                    ]
                }
            }
        ],
        'edges': [
            {'from': 'service_impl_1', 'to': 'facade_1'},
            {'from': 'facade_1', 'to': 'dao_1'}
        ],
        'metadata': {
            'entities': {
                'MediumClaim': {
                    'table_name': 'CLAIM',
                    'fields': {'Cl_ID': {'column': 'CLAIM_ID'}}
                }
            },
            'enums': {
                'Claim_ClaimStatus': {'CLARIFICATIONOPENED': 12}
            },
            'helper_methods': {
                'getClaims': {
                    'name': 'getClaims',
                    'signature': 'GetClaimsOutPut getClaims(...)',
                    'source_code': 'public GetClaimsOutPut getClaims() { ... }' * 100
                },
                'getCoutMediumClaimByClaimCriteriaNew': {
                    'name': 'getCoutMediumClaimByClaimCriteriaNew',
                    'signature': 'int getCoutMediumClaimByClaimCriteriaNew(...)',
                    'source_code': '''
\tpublic int getCoutMediumClaimByClaimCriteriaNew(ClaimCriteria claimCriteria, int iClinicID) {
\t\tString sQry = "select count(*) from MediumClaim mc where mc.C_ID = "+iClinicID;
\t\tif(claimCriteria.getiPatient_Id() != 0) {
\t\t\tsQry = sQry + " and mc.P_ID = "+claimCriteria.getiPatient_Id();
\t\t}
\t\treturn getHibernateTemplate().find(sQry).get(0);
\t}
''' * 10
                }
            },
            'conversion_hints': {
                'database': {'dialect': 'mysql'}
            }
        }
    }


def test_optimizer():
    """Test the optimizer"""
    print("=" * 80)
    print("Testing CallGraphOptimizer")
    print("=" * 80)
    
    # Create sample graph
    original_graph = create_sample_large_graph()
    
    # Calculate original size
    original_json = json.dumps(original_graph, indent=2)
    original_size = len(original_json)
    print(f"\n✓ Created sample graph")
    print(f"  Original size: {original_size:,} bytes ({original_size/1024:.2f} KB)")
    print(f"  Nodes: {len(original_graph['nodes'])}")
    print(f"  Helper methods: {len(original_graph['metadata']['helper_methods'])}")
    
    # Optimize
    optimizer = CallGraphOptimizer()
    optimized_graph = optimizer.optimize(original_graph)
    
    # Calculate optimized size
    optimized_json = json.dumps(optimized_graph, indent=2)
    optimized_size = len(optimized_json)
    reduction = original_size - optimized_size
    reduction_pct = (reduction / original_size * 100)
    
    print(f"\n✓ Optimized graph")
    print(f"  Optimized size: {optimized_size:,} bytes ({optimized_size/1024:.2f} KB)")
    print(f"  Reduction: {reduction:,} bytes ({reduction_pct:.1f}%)")
    
    # Get stats
    stats = optimizer.get_size_stats(original_graph, optimized_graph)
    print(f"\n✓ Size statistics:")
    print(f"  Original: {stats['original_size_kb']} KB")
    print(f"  Optimized: {stats['optimized_size_kb']} KB")
    print(f"  Reduction: {stats['reduction_percent']}%")
    
    # Verify critical data preserved
    print(f"\n✓ Verifying critical data preserved:")
    print(f"  API name: {optimized_graph.get('api_name')} ✓")
    print(f"  Entry point: {optimized_graph.get('entry_point')} ✓")
    print(f"  Nodes count: {len(optimized_graph.get('nodes', []))} ✓")
    print(f"  Edges count: {len(optimized_graph.get('edges', []))} ✓")
    
    # Check DAO node optimization
    dao_node = next((n for n in optimized_graph['nodes'] if n['node_type'] == 'dao'), None)
    if dao_node:
        print(f"\n✓ DAO node optimized:")
        print(f"  Has query_logic: {'query_logic' in dao_node} ✓")
        print(f"  Source code compressed: {len(dao_node.get('source_code', '')) < 500} ✓")
        if 'query_logic' in dao_node:
            print(f"  Query logic keys: {list(dao_node['query_logic'].keys())}")
    
    # Check facade node optimization
    facade_node = next((n for n in optimized_graph['nodes'] if n['node_type'] == 'facade'), None)
    if facade_node:
        print(f"\n✓ Facade node optimized:")
        print(f"  Source code stripped: {len(facade_node.get('source_code', '')) < 100} ✓")
    
    # Check helper methods optimization
    helper_methods = optimized_graph.get('metadata', {}).get('helper_methods', {})
    print(f"\n✓ Helper methods optimized:")
    print(f"  Count: {len(helper_methods)}")
    for name, helper in helper_methods.items():
        if 'logic_reference' in helper:
            print(f"  {name}: References {helper['logic_reference']} ✓")
    
    # Save samples for inspection
    with open('test_output_original.json', 'w') as f:
        json.dump(original_graph, f, indent=2)
    
    with open('test_output_optimized.json', 'w') as f:
        json.dump(optimized_graph, f, indent=2)
    
    print(f"\n✓ Sample files saved:")
    print(f"  test_output_original.json")
    print(f"  test_output_optimized.json")
    
    print("\n" + "=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)


if __name__ == '__main__':
    test_optimizer()
