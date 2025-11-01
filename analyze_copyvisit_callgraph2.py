import json

# Load the full call graph
with open('output/call_graphs/2ac29472-c2bd-409f-b0cf-c344ac66240c_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total nodes in FULL call graph: {len(data.get('nodes', []))}")

# Load the pruned version (what LLM received)
try:
    with open('output/call_graphs/2ac29472-c2bd-409f-b0cf-c344ac66240c.json', 'r', encoding='utf-8') as f:
        pruned_data = json.load(f)
    print(f"Total nodes in PRUNED call graph (sent to LLM): {len(pruned_data.get('nodes', []))}")
    
    print("\n=== PRUNED NODES (what LLM saw) ===")
    for idx, node in enumerate(pruned_data.get('nodes', [])):
        signature = node.get('signature', {})
        method_name = signature.get('name', 'N/A') if isinstance(signature, dict) else 'N/A'
        node_type = node.get('node_type', 'N/A')
        has_source = len(node.get('source_code', '')) > 0
        has_queries = any(kw in node.get('source_code', '') for kw in ['createQuery', 'from ', 'select', 'insert', 'update'])
        
        print(f"{idx+1}. [{node_type}] {method_name}")
        print(f"   Source code: {has_source}, Has DB queries: {has_queries}")
        
except FileNotFoundError:
    print("\nPruned version not found - checking what was sent to LLM...")

# Check for specific critical methods
print("\n=== CRITICAL METHODS IN FULL GRAPH ===")
target_methods = [
    'saveCopyClaimByCopyVisitParams',
    'getCopyClaimInfoBO',
    'storeOrUpdateCopyClaimInfoBO',
    'getCopyVisitDiagnosisAndProcedure',
    'getProvidersAndFacilityByVisitId',
    'getMiscellaneousByVisitId',
    'getCMSOverrideDataByVisitId',
    'storeOrUpdateClaim',
    'storeOrUpdateVisit'
]

for method in target_methods:
    found = [n for n in data.get('nodes', []) if method in str(n.get('signature', ''))]
    if found:
        print(f"FOUND {method}: {len(found)} node(s)")
        for n in found:
            has_queries = any(kw in n.get('source_code', '') for kw in ['createQuery', 'from ', 'select', 'insert', 'update', 'delete', 'session.save', 'session.update'])
            print(f"  - Type: {n.get('node_type')}, Has DB ops: {has_queries}, Source lines: {len(n.get('source_code', '').split(chr(10)))}")
    else:
        print(f"MISSING {method}")
