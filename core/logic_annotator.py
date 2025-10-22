"""
Business Logic Annotator

Analyzes Java source code and adds annotations about complex business logic
patterns to help LLM understand the intent and structure.
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LogicPattern:
    """Represents a detected business logic pattern"""
    pattern_type: str
    description: str
    code_snippet: str
    line_start: int
    line_end: int
    complexity: str  # 'simple', 'moderate', 'complex'


class LogicAnnotator:
    """Annotates business logic patterns in Java code"""
    
    def __init__(self):
        self.patterns: List[LogicPattern] = []
    
    def analyze_method(self, source_code: str, method_name: str) -> Dict:
        """
        Analyze a method's business logic and return annotations
        
        Args:
            source_code: Java method source code
            method_name: Name of the method
            
        Returns:
            Dictionary with logic annotations
        """
        annotations = {
            'method_name': method_name,
            'patterns': [],
            'complexity_score': 0,
            'recommendations': []
        }
        
        # Detect patterns
        self._detect_conditional_query_building(source_code, annotations)
        self._detect_enum_comparisons(source_code, annotations)
        self._detect_helper_method_calls(source_code, annotations)
        self._detect_complex_case_statements(source_code, annotations)
        self._detect_loop_based_string_building(source_code, annotations)
        self._detect_null_checks(source_code, annotations)
        self._detect_date_calculations(source_code, annotations)
        
        # Calculate complexity
        annotations['complexity_score'] = self._calculate_complexity(annotations['patterns'])
        
        # Generate recommendations
        annotations['recommendations'] = self._generate_recommendations(annotations)
        
        return annotations
    
    def _detect_conditional_query_building(self, source: str, annotations: Dict):
        """Detect dynamic query building with conditionals"""
        # Pattern: sQry = sQry + " and ..."
        pattern = r'(\w+)\s*=\s*\1\s*\+\s*["\'].*?["\']'
        matches = list(re.finditer(pattern, source))
        
        if len(matches) > 5:
            annotations['patterns'].append({
                'type': 'conditional_query_building',
                'description': 'Dynamic SQL/HQL query built with multiple conditional appends',
                'count': len(matches),
                'complexity': 'complex',
                'llm_hint': 'Use list of WHERE clauses and JOIN them with AND. Build query string at the end.'
            })
    
    def _detect_enum_comparisons(self, source: str, annotations: Dict):
        """Detect enum comparisons"""
        # Pattern: EnumClass.CONSTANT.getEnumClass()
        pattern = r'(\w+)\.(\w+)\.get\w+\(\)'
        matches = list(re.finditer(pattern, source))
        
        if matches:
            enums_used = set()
            for match in matches:
                enum_class = match.group(1)
                enum_constant = match.group(2)
                enums_used.add(f"{enum_class}.{enum_constant}")
            
            annotations['patterns'].append({
                'type': 'enum_comparisons',
                'description': 'Uses enum constants for comparisons',
                'enums': list(enums_used),
                'complexity': 'moderate',
                'llm_hint': 'Look up enum values in metadata.enums and use integer values directly'
            })
    
    def _detect_helper_method_calls(self, source: str, annotations: Dict):
        """Detect calls to helper methods"""
        # Pattern: this.methodName( or ClassName.methodName(
        patterns = [
            r'this\.(\w+)\s*\(',
            r'(\w+)\.(\w+)\s*\('
        ]
        
        helper_calls = set()
        for pattern in patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                if len(match.groups()) == 1:
                    helper_calls.add(match.group(1))
                else:
                    helper_calls.add(f"{match.group(1)}.{match.group(2)}")
        
        # Filter out common methods
        filtered = [h for h in helper_calls if h not in {
            'get', 'set', 'is', 'equals', 'toString', 'add', 'size', 'length'
        }]
        
        if filtered:
            annotations['patterns'].append({
                'type': 'helper_method_calls',
                'description': 'Calls helper methods whose logic must be included',
                'helpers': filtered,
                'complexity': 'moderate',
                'llm_hint': 'Check metadata.helper_methods for implementations of these methods'
            })
    
    def _detect_complex_case_statements(self, source: str, annotations: Dict):
        """Detect complex CASE WHEN statements"""
        if 'CASE WHEN' in source or 'case when' in source:
            # Count WHEN clauses
            when_count = len(re.findall(r'\bWHEN\b', source, re.IGNORECASE))
            
            annotations['patterns'].append({
                'type': 'complex_case_statement',
                'description': 'SQL CASE statement with multiple WHEN clauses',
                'when_count': when_count,
                'complexity': 'complex' if when_count > 5 else 'moderate',
                'llm_hint': 'Preserve entire CASE statement in SQL query. Use MySQL CASE syntax.'
            })
    
    def _detect_loop_based_string_building(self, source: str, annotations: Dict):
        """Detect loops that build strings (like status lists)"""
        # Pattern: for loop with string concatenation
        pattern = r'for\s*\([^)]+\)\s*\{[^}]*\+\s*["\'][,;]["\'][^}]*\}'
        matches = list(re.finditer(pattern, source, re.DOTALL))
        
        if matches:
            annotations['patterns'].append({
                'type': 'loop_string_building',
                'description': 'Loops that build comma-separated strings',
                'count': len(matches),
                'complexity': 'moderate',
                'llm_hint': 'Use Python list and join() instead of loop concatenation'
            })
    
    def _detect_null_checks(self, source: str, annotations: Dict):
        """Detect null/empty checks"""
        patterns = [
            r'if\s*\([^)]*!=\s*null',
            r'if\s*\([^)]*==\s*null',
            r'\.equals\s*\(\s*""\s*\)',
        ]
        
        null_checks = 0
        for pattern in patterns:
            null_checks += len(re.findall(pattern, source))
        
        if null_checks > 5:
            annotations['patterns'].append({
                'type': 'extensive_null_checks',
                'description': 'Many null/empty validation checks',
                'count': null_checks,
                'complexity': 'simple',
                'llm_hint': 'Use Python "is None" and ".get()" with defaults'
            })
    
    def _detect_date_calculations(self, source: str, annotations: Dict):
        """Detect date calculations"""
        if 'DATEDIFF' in source or 'CURDATE' in source:
            annotations['patterns'].append({
                'type': 'date_calculations',
                'description': 'SQL date calculations (DATEDIFF, CURDATE)',
                'complexity': 'moderate',
                'llm_hint': 'Use MySQL date functions in SQL queries. For Python, use datetime module.'
            })
    
    def _calculate_complexity(self, patterns: List[Dict]) -> int:
        """Calculate overall complexity score"""
        score = 0
        for pattern in patterns:
            if pattern.get('complexity') == 'simple':
                score += 1
            elif pattern.get('complexity') == 'moderate':
                score += 3
            elif pattern.get('complexity') == 'complex':
                score += 5
        return score
    
    def _generate_recommendations(self, annotations: Dict) -> List[str]:
        """Generate recommendations for LLM conversion"""
        recommendations = []
        
        complexity = annotations['complexity_score']
        
        if complexity > 15:
            recommendations.append(
                "HIGH COMPLEXITY: Break this method into multiple code nodes (validation, query building, execution, formatting)"
            )
        elif complexity > 8:
            recommendations.append(
                "MODERATE COMPLEXITY: Consider 2-3 code nodes for this logic"
            )
        
        patterns = annotations['patterns']
        pattern_types = [p['type'] for p in patterns]
        
        if 'conditional_query_building' in pattern_types:
            recommendations.append(
                "Use list-based WHERE clause building: where_clauses = []; if condition: where_clauses.append(...); query += ' AND '.join(where_clauses)"
            )
        
        if 'enum_comparisons' in pattern_types:
            recommendations.append(
                "Replace all enum.getXxx() calls with integer values from metadata.enums"
            )
        
        if 'helper_method_calls' in pattern_types:
            recommendations.append(
                "Include helper method logic inline or reference metadata.helper_methods"
            )
        
        if 'complex_case_statement' in pattern_types:
            recommendations.append(
                "Preserve CASE WHEN statement exactly as-is in SQL query"
            )
        
        return recommendations


def annotate_call_graph_nodes(call_graph: Dict) -> Dict:
    """
    Add logic annotations to all nodes in call graph
    
    Args:
        call_graph: Call graph dictionary
        
    Returns:
        Enhanced call graph with logic_annotations in each node
    """
    annotator = LogicAnnotator()
    
    for node in call_graph.get('nodes', []):
        source_code = node.get('source_code', '')
        method_name = node.get('signature', {}).get('name', 'unknown')
        
        if source_code:
            annotations = annotator.analyze_method(source_code, method_name)
            node['logic_annotations'] = annotations
    
    return call_graph


if __name__ == "__main__":
    # Test
    sample_code = '''
    public MediumClaim[] getMediumClaimByClaimCriteriaNew(ClaimCriteria claimCriteria, int iOffset, int iCount, int iClinicID) {
        String sQry = "select mc from MediumClaim mc where mc.C_ID = " + iClinicID;
        
        if(claimCriteria.getiPatient_Id() != 0) {
            sQry = sQry + " and mc.P_ID = " + claimCriteria.getiPatient_Id();
        }
        
        if(claimCriteria.getBtStatusGroup() != null) {
            ClaimStatus claimStatus = this.getStatusStringNew(claimCriteria.getBtStatusGroup());
            if (claimStatus.isblClaimcreated()) {
                sQry = sQry + " and mc.STATUS = " + Claim_ClaimStatus.CLAIMCREATED.getClaim_ClaimStatus();
            }
        }
        
        return results;
    }
    '''
    
    annotator = LogicAnnotator()
    annotations = annotator.analyze_method(sample_code, "getMediumClaimByClaimCriteriaNew")
    
    print("Logic Annotations:")
    print(f"Complexity Score: {annotations['complexity_score']}")
    print(f"\nPatterns Detected:")
    for pattern in annotations['patterns']:
        print(f"  - {pattern['type']}: {pattern['description']}")
    print(f"\nRecommendations:")
    for rec in annotations['recommendations']:
        print(f"  - {rec}")
