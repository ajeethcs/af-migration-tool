import json

# Load the full call graph
with open('output/call_graphs/2ac29472-c2bd-409f-b0cf-c344ac66240c_full.json', 'r') as f:
    data = json.load(f)

print(f"Total nodes: {len(data.get('nodes', []))}")
print(f"Entry point: {data.get('entry_point')}")
print(f"\nNode structure sample:")
if data.get('nodes'):
    first_node = data['nodes'][0]
    print(f"Keys in first node: {list(first_node.keys())}")
    
print("\n=== Analyzing all nodes ===")
dao_nodes = []
nodes_with_queries = []

for idx, node in enumerate(data.get('nodes', [])):
    node_id = node.get('id', f'node_{idx}')
    signature = node.get('signature', 'N/A')
    node_type = node.get('node_type', 'N/A')
    source_code = node.get('source_code', '')
    
    # Check for DAO nodes
    if node_type == 'dao':
        dao_nodes.append({
            'id': node_id,
            'signature': signature,
            'has_query': any(kw in source_code for kw in ['createQuery', 'from ', 'select', 'insert', 'update', 'delete'])
        })
    
    # Check for database operations
    if any(kw in source_code for kw in ['createQuery', 'getHibernateTemplate', 'session.', 'from ', 'select', 'insert', 'update', 'delete']):
        nodes_with_queries.append({
            'id': node_id,
            'signature': signature,
            'node_type': node_type
        })

print(f"\n=== DAO Nodes: {len(dao_nodes)} ===")
for node in dao_nodes[:10]:
    print(f"  - {node['signature']}")
    print(f"    Has DB query: {node['has_query']}")

print(f"\n=== Nodes with DB operations: {len(nodes_with_queries)} ===")
for node in nodes_with_queries[:10]:
    print(f"  - [{node['node_type']}] {node['signature']}")

# Check specific methods
print("\n=== Looking for specific methods ===")
target_methods = [
    'saveCopyClaimByCopyVisitParams',
    'getCopyClaimInfoBO',
    'storeOrUpdateCopyClaimInfoBO',
    'getCopyVisitDiagnosisAndProcedure',
    'getProvidersAndFacilityByVisitId',
    'getMiscellaneousByVisitId',
    'getCMSOverrideDataByVisitId'
]

for method in target_methods:
    found = [n for n in data.get('nodes', []) if method in n.get('signature', '')]
    if found:
        print(f"✓ Found {method}: {len(found)} node(s)")
        for n in found:
            print(f"    Type: {n.get('node_type')}, Has source: {len(n.get('source_code', '')) > 0}")
    else:
        print(f"✗ Missing {method}")
