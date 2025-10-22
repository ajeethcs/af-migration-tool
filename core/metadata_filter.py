"""
Metadata Filter

Filters schema metadata to include only entities/enums used by a specific API.
This reduces token usage and improves LLM focus.
"""
from typing import Dict, Set, List
import re


class MetadataFilter:
    """Filters metadata to only include relevant entities and enums for an API"""
    
    def __init__(self):
        self.used_entities: Set[str] = set()
        self.used_enums: Set[str] = set()
    
    def filter_metadata_for_api(
        self, 
        call_graph: Dict, 
        full_metadata: Dict
    ) -> Dict:
        """
        Filter metadata to only include entities/enums used in this call graph
        
        Args:
            call_graph: The call graph with nodes and edges
            full_metadata: Complete metadata with all entities/enums
            
        Returns:
            Filtered metadata with only relevant entities/enums
        """
        print("\n" + "="*70)
        print("FILTERING METADATA FOR API")
        print("="*70)
        
        # Reset tracking
        self.used_entities.clear()
        self.used_enums.clear()
        
        # Scan all nodes for entity/enum references
        for node in call_graph.get('nodes', []):
            source_code = node.get('source_code', '')
            if source_code:
                self._scan_for_entities(source_code, full_metadata.get('entities', {}))
                self._scan_for_enums(source_code, full_metadata.get('enums', {}))
        
        # Build filtered metadata
        filtered = {
            'entities': {},
            'enums': {},
            'database': full_metadata.get('database', {})
        }
        
        # Add only used entities
        all_entities = full_metadata.get('entities', {})
        for entity_name in self.used_entities:
            if entity_name in all_entities:
                filtered['entities'][entity_name] = all_entities[entity_name]
        
        # Add only used enums
        all_enums = full_metadata.get('enums', {})
        for enum_name in self.used_enums:
            if enum_name in all_enums:
                filtered['enums'][enum_name] = all_enums[enum_name]
        
        # Copy helper methods and conversion hints (always relevant)
        if 'helper_methods' in full_metadata:
            filtered['helper_methods'] = full_metadata['helper_methods']
        if 'conversion_hints' in full_metadata:
            filtered['conversion_hints'] = full_metadata['conversion_hints']
        
        # Print statistics
        total_entities = len(all_entities)
        total_enums = len(all_enums)
        used_entities = len(filtered['entities'])
        used_enums = len(filtered['enums'])
        
        print(f"\n📊 Filtering Results:")
        print(f"  Entities: {used_entities}/{total_entities} ({self._percentage(used_entities, total_entities)}%)")
        print(f"  Enums: {used_enums}/{total_enums} ({self._percentage(used_enums, total_enums)}%)")
        
        if used_entities < total_entities:
            print(f"\n✓ Reduced metadata size by ~{100 - self._percentage(used_entities + used_enums, total_entities + total_enums)}%")
        
        print("\n  Used entities:", ', '.join(sorted(self.used_entities)[:10]))
        if len(self.used_entities) > 10:
            print(f"  ... and {len(self.used_entities) - 10} more")
        
        print("="*70)
        
        return filtered
    
    def _scan_for_entities(self, source_code: str, all_entities: Dict):
        """Scan source code for entity references"""
        # Pattern 1: HQL queries - "from EntityName"
        hql_pattern = r'\bfrom\s+(\w+)\b'
        for match in re.finditer(hql_pattern, source_code):
            entity_name = match.group(1)
            if entity_name in all_entities:
                self.used_entities.add(entity_name)
        
        # Pattern 2: Direct entity class usage - "new EntityName()"
        new_pattern = r'\bnew\s+(\w+)\s*\('
        for match in re.finditer(new_pattern, source_code):
            entity_name = match.group(1)
            if entity_name in all_entities:
                self.used_entities.add(entity_name)
        
        # Pattern 3: Entity type declarations - "EntityName entity"
        for entity_name in all_entities.keys():
            # Look for the entity name as a type
            type_pattern = rf'\b{entity_name}\b\s+\w+'
            if re.search(type_pattern, source_code):
                self.used_entities.add(entity_name)
        
        # Pattern 4: Generic types - "List<EntityName>"
        generic_pattern = r'<(\w+)>'
        for match in re.finditer(generic_pattern, source_code):
            entity_name = match.group(1)
            if entity_name in all_entities:
                self.used_entities.add(entity_name)
    
    def _scan_for_enums(self, source_code: str, all_enums: Dict):
        """Scan source code for enum references"""
        # Pattern 1: Enum.CONSTANT usage
        for enum_name in all_enums.keys():
            enum_pattern = rf'\b{enum_name}\.\w+'
            if re.search(enum_pattern, source_code):
                self.used_enums.add(enum_name)
        
        # Pattern 2: Enum type declarations
        for enum_name in all_enums.keys():
            type_pattern = rf'\b{enum_name}\b\s+\w+'
            if re.search(type_pattern, source_code):
                self.used_enums.add(enum_name)
    
    def _percentage(self, part: int, total: int) -> int:
        """Calculate percentage"""
        if total == 0:
            return 0
        return int((part / total) * 100)


def filter_metadata(call_graph: Dict) -> Dict:
    """
    Convenience function to filter metadata in a call graph
    
    Args:
        call_graph: Call graph with metadata
        
    Returns:
        Call graph with filtered metadata
    """
    if 'metadata' not in call_graph:
        return call_graph
    
    full_metadata = call_graph['metadata']
    
    # Skip filtering if metadata is already small
    entity_count = len(full_metadata.get('entities', {}))
    enum_count = len(full_metadata.get('enums', {}))
    
    if entity_count + enum_count < 20:
        print(f"ℹ Metadata is small ({entity_count} entities, {enum_count} enums), skipping filtering")
        return call_graph
    
    # Filter metadata
    filterer = MetadataFilter()
    filtered_metadata = filterer.filter_metadata_for_api(call_graph, full_metadata)
    
    # Update call graph
    call_graph['metadata'] = filtered_metadata
    
    return call_graph


if __name__ == "__main__":
    # Test with a sample call graph
    import json
    from pathlib import Path
    
    # Load a test call graph
    test_file = Path("output/call_graphs/enhanced_with_business_logic.json")
    
    if test_file.exists():
        with open(test_file, 'r') as f:
            call_graph = json.load(f)
        
        print("Original metadata:")
        print(f"  Entities: {len(call_graph.get('metadata', {}).get('entities', {}))}")
        print(f"  Enums: {len(call_graph.get('metadata', {}).get('enums', {}))}")
        
        # Filter
        filtered = filter_metadata(call_graph)
        
        print("\nFiltered metadata:")
        print(f"  Entities: {len(filtered.get('metadata', {}).get('entities', {}))}")
        print(f"  Enums: {len(filtered.get('metadata', {}).get('enums', {}))}")
        
        # Save filtered version
        output_file = Path("output/call_graphs/filtered_metadata.json")
        with open(output_file, 'w') as f:
            json.dump(filtered, f, indent=2)
        
        print(f"\n✓ Saved filtered call graph to: {output_file}")
    else:
        print(f"Test file not found: {test_file}")
        print("Run the call graph builder first to generate test data")
