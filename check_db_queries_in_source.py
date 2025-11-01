import json

# Load the pruned call graph (what LLM received)
with open('output/call_graphs/2ac29472-c2bd-409f-b0cf-c344ac66240c.json', 'r', encoding='utf-8') as f:
    pruned_data = json.load(f)

print(f"=== CHECKING DB QUERIES IN SOURCE CODE (PRUNED GRAPH) ===\n")
print(f"Total nodes: {len(pruned_data.get('nodes', []))}\n")

# Check critical DAO methods for actual DB queries in their source code
critical_methods = [
    'saveCopyClaimByCopyVisitParams',
    'getCopyClaimInfoBO',
    'storeOrUpdateCopyClaimInfoBO',
    'getCopyVisitByVisitId',
    'getCopyClaimByClaimId',
    'getVisitDiagnosis',
    'getCopyVisitProcedureByClaimId',
    'getMiscellaneousByVisitId',
    'getCMSOverrideDataByVisitId',
    'getProvidersAndFacilityByVisitId',
    'storeOrUpdateCopyVisit',
    'storeOrUpdateCopyClaim',
    'storeOrUpdateVisit',
    'storeOrUpdateClaim'
]

db_keywords = ['createQuery', 'getHibernateTemplate', 'session.save', 'session.update', 
               'session.delete', 'from ', 'select ', 'insert ', 'update ', 'delete ']

for method_name in critical_methods:
    print(f"\n{'='*80}")
    print(f"METHOD: {method_name}")
    print('='*80)
    
    found_nodes = [n for n in pruned_data.get('nodes', []) 
                   if n.get('signature', {}).get('name') == method_name]
    
    if not found_nodes:
        print(f"  ❌ NOT FOUND in pruned graph")
        continue
    
    for node in found_nodes:
        node_type = node.get('node_type', 'N/A')
        source_code = node.get('source_code', '')
        
        print(f"\n  Node Type: {node_type}")
        print(f"  Source Code Length: {len(source_code)} chars")
        
        # Check for DB operations
        has_db_ops = any(kw in source_code for kw in db_keywords)
        print(f"  Has DB Operations: {has_db_ops}")
        
        if has_db_ops:
            print(f"\n  DB Operations Found:")
            for kw in db_keywords:
                if kw in source_code:
                    # Find lines with this keyword
                    lines = source_code.split('\n')
                    for i, line in enumerate(lines):
                        if kw in line:
                            print(f"    Line {i+1}: {line.strip()[:100]}")
        else:
            # Show first 20 lines of source to see what's there
            print(f"\n  Source Code Preview (first 500 chars):")
            print(f"  {source_code[:500]}")
            
            # Check for method calls instead
            if 'this.' in source_code or '.' in source_code:
                print(f"\n  Method Calls Found:")
                lines = source_code.split('\n')
                for i, line in enumerate(lines[:20]):
                    if 'this.' in line or ('=' in line and '(' in line):
                        print(f"    Line {i+1}: {line.strip()}")

print(f"\n\n{'='*80}")
print("SUMMARY")
print('='*80)

nodes_with_db = []
nodes_without_db = []

for node in pruned_data.get('nodes', []):
    source_code = node.get('source_code', '')
    method_name = node.get('signature', {}).get('name', 'N/A')
    node_type = node.get('node_type', 'N/A')
    
    has_db = any(kw in source_code for kw in db_keywords)
    
    if has_db:
        nodes_with_db.append(method_name)
    else:
        if node_type == 'dao':
            nodes_without_db.append(method_name)

print(f"\nNodes WITH direct DB operations: {len(nodes_with_db)}")
print(f"DAO nodes WITHOUT direct DB operations: {len(nodes_without_db)}")
print(f"\nThis means {len(nodes_without_db)} DAO methods delegate to other methods")
print(f"The LLM needs to trace through dependencies to find actual DB operations")
