"""
Business Logic Enhancer

Comprehensive enhancement of call graphs with all business logic context
needed for accurate LLM conversion.
"""
from pathlib import Path
from typing import Dict, List
import json

from core.schema_extractor import extract_metadata
from core.helper_extractor import HelperMethodExtractor
from core.logic_annotator import LogicAnnotator
from core.metadata_filter import MetadataFilter
from config import ALLOFACTOR_SRC, DAO_PATH


class BusinessLogicEnhancer:
    """Enhances call graphs with complete business logic context"""
    
    def __init__(self):
        self.helper_extractor = HelperMethodExtractor()
        self.logic_annotator = LogicAnnotator()
        self.metadata_filter = MetadataFilter()
    
    def enhance_call_graph(self, call_graph: Dict, include_all: bool = True, filter_metadata: bool = True) -> Dict:
        """
        Enhance call graph with all business logic metadata
        
        Args:
            call_graph: Base call graph from CallGraphBuilder
            include_all: Include all enhancements (schema, helpers, annotations)
            filter_metadata: Filter metadata to only include entities/enums used by this API
            
        Returns:
            Fully enhanced call graph
        """
        print("\n" + "="*70)
        print("ENHANCING CALL GRAPH WITH BUSINESS LOGIC CONTEXT")
        print("="*70)
        
        enhanced = call_graph.copy()
        
        if include_all:
            # 1. Schema metadata (already included by CallGraphBuilder)
            if 'entities' not in enhanced.get('metadata', {}):
                print("\n1. Adding schema metadata...")
                enhanced = self._add_schema_metadata(enhanced)
            else:
                print("\n1. Schema metadata already present ✓")
            
            # 2. Helper methods
            print("\n2. Extracting helper methods...")
            enhanced = self._add_helper_methods(enhanced)
            
            # 3. Logic annotations
            print("\n3. Annotating business logic patterns...")
            enhanced = self._add_logic_annotations(enhanced)
            
            # 4. Conversion hints
            print("\n4. Adding LLM conversion hints...")
            enhanced = self._add_conversion_hints(enhanced)
            
            # 5. Filter metadata (optional)
            if filter_metadata and 'metadata' in enhanced:
                print("\n5. Filtering metadata to API-specific entities/enums...")
                enhanced = self._filter_metadata(enhanced)
            else:
                print("\n5. Skipping metadata filtering (using all entities/enums)")
        
        print("\n" + "="*70)
        print("ENHANCEMENT COMPLETE")
        print("="*70)
        
        return enhanced
    
    def _add_schema_metadata(self, call_graph: Dict) -> Dict:
        """Add database schema metadata"""
        hibernate_maps = DAO_PATH / "hibernate" / "maps"
        
        if not hibernate_maps.exists():
            print("  ⚠ Hibernate maps not found, skipping schema metadata")
            return call_graph
        
        metadata = extract_metadata(
            hibernate_maps_path=hibernate_maps,
            java_source_paths=[ALLOFACTOR_SRC]
        )
        
        if 'metadata' not in call_graph:
            call_graph['metadata'] = {}
        
        call_graph['metadata'].update(metadata)
        
        print(f"  ✓ Added {len(metadata.get('entities', {}))} entity mappings")
        print(f"  ✓ Added {len(metadata.get('enums', {}))} enum definitions")
        
        return call_graph
    
    def _add_helper_methods(self, call_graph: Dict) -> Dict:
        """Extract and add helper method implementations"""
        all_helpers = {}
        helper_count = 0
        
        for node in call_graph.get('nodes', []):
            if node.get('node_type') in ['dao', 'service_impl']:
                source_code = node.get('source_code', '')
                file_path = node.get('file_path', '')
                
                if not source_code or not file_path:
                    continue
                
                # Find helper calls in this node
                helper_calls = self.helper_extractor.find_helper_calls_in_source(source_code)
                
                if helper_calls:
                    # Extract those helpers
                    try:
                        helpers = self.helper_extractor.extract_helpers_from_class(
                            Path(file_path),
                            helper_calls
                        )
                        all_helpers.update(helpers)
                        helper_count += len(helpers)
                    except Exception as e:
                        print(f"  ⚠ Could not extract helpers from {file_path}: {e}")
        
        if all_helpers:
            if 'metadata' not in call_graph:
                call_graph['metadata'] = {}
            call_graph['metadata']['helper_methods'] = all_helpers
            print(f"  ✓ Extracted {helper_count} helper methods")
        else:
            print(f"  ℹ No helper methods found")
        
        return call_graph
    
    def _add_logic_annotations(self, call_graph: Dict) -> Dict:
        """Add business logic pattern annotations to nodes"""
        annotated_count = 0
        total_complexity = 0
        
        for node in call_graph.get('nodes', []):
            source_code = node.get('source_code', '')
            method_name = node.get('signature', {}).get('name', 'unknown')
            
            if source_code:
                annotations = self.logic_annotator.analyze_method(source_code, method_name)
                node['logic_annotations'] = annotations
                annotated_count += 1
                total_complexity += annotations.get('complexity_score', 0)
        
        if annotated_count > 0:
            avg_complexity = total_complexity / annotated_count
            print(f"  ✓ Annotated {annotated_count} nodes")
            print(f"  ℹ Average complexity score: {avg_complexity:.1f}")
        
        return call_graph
    
    def _add_conversion_hints(self, call_graph: Dict) -> Dict:
        """Add top-level conversion hints for LLM"""
        hints = {
            'database': {
                'dialect': 'mysql',
                'orm_source': 'hibernate',
                'orm_target': 'sqlalchemy',
                'query_style': 'Use text() for raw SQL with parameterized queries'
            },
            'code_style': {
                'naming': 'Use snake_case for Python variables and functions',
                'error_handling': 'Use try/except with specific error types',
                'null_handling': 'Use "is None" and .get() with defaults'
            },
            'architecture': {
                'pattern': 'Split into validation → business logic → persistence → formatting nodes',
                'data_flow': 'Pass {"ok": bool, "data": any} between nodes',
                'final_node': 'Always format to STANDARD_RESPONSE'
            },
            'critical_rules': [
                'ALWAYS use metadata.entities for table/column name lookups',
                'ALWAYS use metadata.enums for enum value lookups',
                'ALWAYS check metadata.helper_methods for helper implementations',
                'PRESERVE all conditional logic branches from Java',
                'PRESERVE all business rules and validations',
                'Use parameterized queries to prevent SQL injection'
            ]
        }
        
        if 'metadata' not in call_graph:
            call_graph['metadata'] = {}
        
        call_graph['metadata']['conversion_hints'] = hints
        
        print(f"  ✓ Added conversion hints")
        
        return call_graph
    
    def _filter_metadata(self, call_graph: Dict) -> Dict:
        """Filter metadata to only include entities/enums used by this API"""
        full_metadata = call_graph['metadata']
        
        # Skip filtering if metadata is already small
        entity_count = len(full_metadata.get('entities', {}))
        enum_count = len(full_metadata.get('enums', {}))
        
        if entity_count + enum_count < 20:
            print(f"  ℹ Metadata is small ({entity_count} entities, {enum_count} enums), skipping filtering")
            return call_graph
        
        # Filter to only used entities/enums
        filtered_metadata = self.metadata_filter.filter_metadata_for_api(
            call_graph, 
            full_metadata
        )
        
        call_graph['metadata'] = filtered_metadata
        
        return call_graph
    
    def generate_summary_report(self, call_graph: Dict) -> str:
        """Generate a human-readable summary of the enhanced call graph"""
        lines = []
        lines.append("="*70)
        lines.append("ENHANCED CALL GRAPH SUMMARY")
        lines.append("="*70)
        
        # Basic info
        lines.append(f"\nAPI: {call_graph.get('api_name', 'unknown')}")
        lines.append(f"Service: {call_graph.get('service_name', 'unknown')}")
        lines.append(f"Total Nodes: {len(call_graph.get('nodes', []))}")
        lines.append(f"Total Edges: {len(call_graph.get('edges', []))}")
        
        # Metadata summary
        metadata = call_graph.get('metadata', {})
        
        if 'entities' in metadata:
            lines.append(f"\n📊 Database Schema:")
            lines.append(f"  - Entities: {len(metadata['entities'])}")
            lines.append(f"  - Sample entities: {', '.join(list(metadata['entities'].keys())[:5])}")
        
        if 'enums' in metadata:
            lines.append(f"\n🔢 Enum Definitions:")
            lines.append(f"  - Enums: {len(metadata['enums'])}")
            lines.append(f"  - Sample enums: {', '.join(list(metadata['enums'].keys())[:5])}")
        
        if 'helper_methods' in metadata:
            lines.append(f"\n🔧 Helper Methods:")
            lines.append(f"  - Helpers: {len(metadata['helper_methods'])}")
            lines.append(f"  - Sample helpers: {', '.join(list(metadata['helper_methods'].keys())[:5])}")
        
        # Logic complexity
        lines.append(f"\n📈 Business Logic Complexity:")
        total_complexity = 0
        complex_nodes = []
        
        for node in call_graph.get('nodes', []):
            annotations = node.get('logic_annotations', {})
            complexity = annotations.get('complexity_score', 0)
            total_complexity += complexity
            
            if complexity > 10:
                node_name = node.get('signature', {}).get('name', 'unknown')
                complex_nodes.append((node_name, complexity))
        
        lines.append(f"  - Total complexity: {total_complexity}")
        lines.append(f"  - Average per node: {total_complexity / max(len(call_graph.get('nodes', [])), 1):.1f}")
        
        if complex_nodes:
            lines.append(f"\n  ⚠ High complexity nodes:")
            for name, score in sorted(complex_nodes, key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"    - {name}: {score}")
        
        # Recommendations
        lines.append(f"\n💡 Conversion Recommendations:")
        all_recommendations = set()
        for node in call_graph.get('nodes', []):
            annotations = node.get('logic_annotations', {})
            for rec in annotations.get('recommendations', []):
                all_recommendations.add(rec)
        
        for rec in list(all_recommendations)[:5]:
            lines.append(f"  - {rec}")
        
        lines.append("\n" + "="*70)
        
        return "\n".join(lines)


def enhance_and_save(
    call_graph: Dict,
    output_path: Path,
    generate_report: bool = True
) -> Dict:
    """
    Enhance call graph and save to file
    
    Args:
        call_graph: Base call graph
        output_path: Path to save enhanced JSON
        generate_report: Whether to generate summary report
        
    Returns:
        Enhanced call graph
    """
    enhancer = BusinessLogicEnhancer()
    enhanced = enhancer.enhance_call_graph(call_graph)
    
    # Save JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(enhanced, f, indent=2)
    
    print(f"\n✓ Enhanced call graph saved to: {output_path}")
    
    # Generate report
    if generate_report:
        report = enhancer.generate_summary_report(enhanced)
        print("\n" + report)
        
        report_path = output_path.with_suffix('.report.txt')
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"✓ Summary report saved to: {report_path}")
    
    return enhanced


if __name__ == "__main__":
    # Test with existing call graph
    from core.call_graph_builder import CallGraphBuilder
    
    print("Building call graph...")
    builder = CallGraphBuilder()
    call_graph = builder.build_call_graph(
        service_name="ClaimService",
        api_name="getClaims",
        include_schema=True
    )
    
    print("\nEnhancing with business logic...")
    enhanced = enhance_and_save(
        call_graph.model_dump(),
        Path("output/call_graphs/enhanced_with_business_logic.json"),
        generate_report=True
    )
