"""
Test script to prune call graph and check size reduction
"""
import json
import copy

def prune_call_graph_for_llm(call_graph: dict) -> dict:
    """
    Prune call graph to remove absolutely useless fields for LLM code conversion.
    """
    pruned = copy.deepcopy(call_graph)
    
    # Remove top-level useless fields
    pruned.pop('migration_id', None)
    pruned.pop('status', None)
    pruned.pop('message', None)
    pruned.pop('errors', None)
    pruned.pop('edges', None)  # Redundant - already in dependencies
    
    # Prune each node
    if 'nodes' in pruned and isinstance(pruned['nodes'], list):
        for node in pruned['nodes']:
            # Remove useless fields from each node
            node.pop('logic_annotations', None)  # Redundant hints
            node.pop('converted_code', None)     # Always null
            node.pop('file_path', None)          # Only for debugging
            node.pop('line_number', None)        # Only for debugging
            
            # Prune signature fields
            if 'signature' in node and isinstance(node['signature'], dict):
                node['signature'].pop('annotations', None)  # Usually empty
                node['signature'].pop('modifiers', None)    # Not needed for Python
                node['signature'].pop('throws', None)       # Not needed for Python
            
            # Keep: id, name, class_name, node_type, signature, source_code, dependencies
    
    # Prune metadata
    if 'metadata' in pruned and isinstance(pruned['metadata'], dict):
        pruned['metadata'].pop('conversion_hints', None)  # Redundant
        pruned['metadata'].pop('database', None)          # Not needed
        # Keep: entities, enums, helper_methods, dtos
    
    return pruned


if __name__ == "__main__":
    # Load original
    print("Loading original migration.txt...")
    with open('C:/Users/pc/Desktop/migration.txt', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Prune
    print("Pruning...")
    pruned = prune_call_graph_for_llm(data)
    
    # Save pruned version
    print("Saving pruned version...")
    with open('C:/Users/pc/Desktop/migration_pruned.txt', 'w', encoding='utf-8') as f:
        json.dump(pruned, f, indent=2)
    
    # Calculate sizes
    original_str = json.dumps(data)
    pruned_str = json.dumps(pruned)
    
    original_size = len(original_str)
    pruned_size = len(pruned_str)
    reduction = ((1 - pruned_size / original_size) * 100)
    
    # Estimate tokens (rough: 1 token ≈ 4 characters)
    original_tokens = original_size // 4
    pruned_tokens = pruned_size // 4
    
    print("\n" + "="*60)
    print("PRUNING RESULTS")
    print("="*60)
    print(f"Original size:     {original_size:,} characters")
    print(f"Pruned size:       {pruned_size:,} characters")
    print(f"Reduction:         {reduction:.1f}%")
    print(f"Saved:             {original_size - pruned_size:,} characters")
    print()
    print(f"Original tokens:   ~{original_tokens:,} tokens (estimated)")
    print(f"Pruned tokens:     ~{pruned_tokens:,} tokens (estimated)")
    print(f"Token reduction:   ~{original_tokens - pruned_tokens:,} tokens")
    print()
    print(f"gpt-5-mini limit:  272,000 tokens")
    if pruned_tokens < 272000:
        print(f"Status:            FITS! ({272000 - pruned_tokens:,} tokens under limit)")
    else:
        print(f"Status:            STILL TOO LARGE ({pruned_tokens - 272000:,} tokens over limit)")
    print("="*60)
    
    # Verify critical fields preserved
    print("\nVERIFYING CRITICAL FIELDS...")
    # Handle both wrapped and unwrapped structures
    if 'call_graph' in pruned:
        sample_node = pruned['call_graph']['nodes'][0] if pruned['call_graph'].get('nodes') else {}
        metadata = pruned['call_graph'].get('metadata', {})
    else:
        sample_node = pruned['nodes'][0] if pruned.get('nodes') else {}
        metadata = pruned.get('metadata', {})
    
    checks = {
        'source_code': 'source_code' in sample_node,
        'signature': 'signature' in sample_node,
        'name': 'name' in sample_node,
        'dependencies': 'dependencies' in sample_node,
        'metadata.entities': 'entities' in metadata,
        'metadata.enums': 'enums' in metadata,
    }
    
    for field, present in checks.items():
        status = '[OK]' if present else '[MISSING]'
        print(f"{status} {field}: {'Preserved' if present else 'MISSING!'}")
    
    # Verify useless fields removed
    print("\nVERIFYING USELESS FIELDS REMOVED...")
    removed_checks = {
        'logic_annotations': 'logic_annotations' not in sample_node,
        'converted_code': 'converted_code' not in sample_node,
        'file_path': 'file_path' not in sample_node,
        'line_number': 'line_number' not in sample_node,
    }
    
    for field, removed in removed_checks.items():
        status = '[OK]' if removed else '[STILL PRESENT]'
        print(f"{status} {field}: {'Removed' if removed else 'STILL PRESENT!'}")
    
    print("\nPruned file saved to: C:/Users/pc/Desktop/migration_pruned.txt")
