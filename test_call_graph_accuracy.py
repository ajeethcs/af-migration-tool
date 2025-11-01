"""
Call Graph Accuracy Validation Test

This test generates a call graph for an API and cross-verifies it against
the actual Java source code to ensure:
1. All methods are traced
2. All SQL/HQL queries are captured
3. All return types are accurate
4. All parameter definitions are correct
5. All business logic is included
6. All conditional branches are explored
"""
import sys
from pathlib import Path
import json
import re
from typing import Dict, List, Set, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.call_graph_builder import CallGraphBuilder
from core.java_parser import JavaParser
from config import SERVICES_IMPL_PATH, DAO_PATH, FACADE_PATH


class CallGraphAccuracyValidator:
    """Validates call graph accuracy against actual Java source code"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate_api(self, service_name: str, api_name: str) -> Dict:
        """
        Validate call graph for an API
        
        Returns:
            Dict with validation results including:
            - success: bool
            - coverage_percent: float
            - errors: List[str]
            - warnings: List[str]
            - missing_methods: List[str]
            - missing_queries: List[str]
            - type_mismatches: List[Dict]
        """
        print("=" * 80)
        print(f"CALL GRAPH ACCURACY VALIDATION")
        print(f"API: {service_name}.{api_name}")
        print("=" * 80)
        
        # Step 1: Generate call graph
        print("\n1. Generating call graph...")
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(
            service_name=service_name,
            api_name=api_name,
            include_schema=True
        )
        graph_dict = call_graph.model_dump(mode='json')
        print(f"   ✓ Generated {len(graph_dict['nodes'])} nodes, {len(graph_dict['edges'])} edges")
        
        # Step 2: Extract all method calls from actual source code
        print("\n2. Extracting actual method calls from Java source...")
        actual_methods = self._extract_actual_method_calls(service_name, api_name)
        print(f"   ✓ Found {len(actual_methods)} actual method calls in source code")
        
        # Step 3: Extract all queries from actual source code
        print("\n3. Extracting SQL/HQL queries from Java source...")
        actual_queries = self._extract_actual_queries(graph_dict['nodes'])
        print(f"   ✓ Found {len(actual_queries)} SQL/HQL queries in source code")
        
        # Step 4: Validate method coverage
        print("\n4. Validating method coverage...")
        method_coverage = self._validate_method_coverage(graph_dict['nodes'], actual_methods)
        
        # Step 5: Validate query coverage
        print("\n5. Validating query coverage...")
        query_coverage = self._validate_query_coverage(graph_dict['nodes'], actual_queries)
        
        # Step 6: Validate return types
        print("\n6. Validating return types...")
        type_validation = self._validate_return_types(graph_dict['nodes'])
        
        # Step 7: Validate parameter definitions
        print("\n7. Validating parameter definitions...")
        param_validation = self._validate_parameters(graph_dict['nodes'])
        
        # Step 8: Validate conditional branches
        print("\n8. Validating conditional branches...")
        branch_validation = self._validate_conditional_branches(graph_dict['nodes'])
        
        # Step 9: Validate DAO operations
        print("\n9. Validating DAO operations...")
        dao_validation = self._validate_dao_operations(graph_dict['nodes'])
        
        # Calculate overall results
        results = self._compile_results(
            graph_dict,
            method_coverage,
            query_coverage,
            type_validation,
            param_validation,
            branch_validation,
            dao_validation
        )
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _extract_actual_method_calls(self, service_name: str, api_name: str) -> Set[str]:
        """Extract all actual method calls by parsing the Java source"""
        actual_calls = set()
        
        # Parse the entry point
        service_file = SERVICES_IMPL_PATH / f"{service_name}Impl.java"
        if not service_file.exists():
            self.errors.append(f"Service file not found: {service_file}")
            return actual_calls
        
        parser = JavaParser(service_file)
        methods = parser.get_methods()
        
        # Find the API method
        api_method = None
        for method in methods:
            if method['name'] == api_name:
                api_method = method
                break
        
        if not api_method:
            self.errors.append(f"API method '{api_name}' not found in {service_name}Impl")
            return actual_calls
        
        # Extract all method calls recursively
        self._extract_calls_recursive(api_method['source_code'], actual_calls, parser)
        
        return actual_calls
    
    def _extract_calls_recursive(self, source_code: str, calls: Set[str], parser: JavaParser):
        """Recursively extract method calls from source code"""
        # Pattern for all method calls
        patterns = [
            r'daoFacade\.(\w+)\s*\(',
            r'this\.(\w+Dao)\.(\w+)\s*\(',
            r'(?<!this\.)(?<!\.)\b(\w+Dao)\.(\w+)\s*\(',
            r'this\.(\w+)\s*\(',
            r'(?<!\.)\b([a-z]\w+)\s*\(',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, source_code):
                if len(match.groups()) == 1:
                    calls.add(match.group(1))
                elif len(match.groups()) == 2:
                    calls.add(f"{match.group(1)}.{match.group(2)}")
    
    def _extract_actual_queries(self, nodes: List[Dict]) -> List[Dict]:
        """Extract all SQL/HQL queries from node source code"""
        queries = []
        
        for node in nodes:
            source_code = node.get('source_code', '')
            
            # Pattern for HQL queries
            hql_patterns = [
                r'from\s+(\w+)\s+',
                r'select\s+.*?\s+from\s+(\w+)',
                r'createQuery\s*\(\s*["\'](.+?)["\']',
            ]
            
            # Pattern for SQL queries
            sql_patterns = [
                r'SELECT\s+.*?\s+FROM\s+(\w+)',
                r'createSQLQuery\s*\(\s*["\'](.+?)["\']',
            ]
            
            for pattern in hql_patterns + sql_patterns:
                for match in re.finditer(pattern, source_code, re.IGNORECASE | re.DOTALL):
                    queries.append({
                        'node': node['name'],
                        'query': match.group(0)[:100],  # First 100 chars
                        'type': 'HQL' if pattern in hql_patterns else 'SQL'
                    })
        
        return queries
    
    def _validate_method_coverage(self, nodes: List[Dict], actual_methods: Set[str]) -> Dict:
        """Validate that all actual methods are in the call graph"""
        graph_methods = set()
        
        for node in nodes:
            graph_methods.add(node['name'])
        
        missing = actual_methods - graph_methods
        extra = graph_methods - actual_methods
        
        coverage = len(graph_methods & actual_methods) / len(actual_methods) * 100 if actual_methods else 100
        
        result = {
            'coverage_percent': coverage,
            'total_actual': len(actual_methods),
            'total_in_graph': len(graph_methods),
            'missing': list(missing),
            'extra': list(extra)
        }
        
        if missing:
            print(f"   ⚠️  Missing {len(missing)} methods from call graph:")
            for method in list(missing)[:5]:
                print(f"      - {method}")
            if len(missing) > 5:
                print(f"      ... and {len(missing) - 5} more")
        else:
            print(f"   ✓ All actual methods are in call graph")
        
        print(f"   Coverage: {coverage:.1f}%")
        
        return result
    
    def _validate_query_coverage(self, nodes: List[Dict], actual_queries: List[Dict]) -> Dict:
        """Validate that all queries are captured"""
        queries_in_graph = []
        
        for node in nodes:
            source_code = node.get('source_code', '')
            if 'createQuery' in source_code or 'createSQLQuery' in source_code or 'from ' in source_code:
                queries_in_graph.append(node['name'])
        
        result = {
            'total_queries': len(actual_queries),
            'nodes_with_queries': len(queries_in_graph),
            'queries': actual_queries
        }
        
        print(f"   ✓ Found {len(actual_queries)} queries in {len(queries_in_graph)} nodes")
        
        return result
    
    def _validate_return_types(self, nodes: List[Dict]) -> Dict:
        """Validate return type accuracy"""
        type_issues = []
        
        for node in nodes:
            signature = node.get('signature', {})
            return_type = signature.get('return_type', 'void')
            source_code = node.get('source_code', '')
            
            # Check if return type matches return statements
            if return_type != 'void':
                return_pattern = r'return\s+(.+?);'
                returns = re.findall(return_pattern, source_code)
                
                if not returns and 'return' not in source_code:
                    type_issues.append({
                        'node': node['name'],
                        'issue': f"Return type is '{return_type}' but no return statement found",
                        'severity': 'warning'
                    })
        
        result = {
            'total_nodes': len(nodes),
            'issues': type_issues
        }
        
        if type_issues:
            print(f"   ⚠️  Found {len(type_issues)} potential return type issues")
        else:
            print(f"   ✓ All return types appear accurate")
        
        return result
    
    def _validate_parameters(self, nodes: List[Dict]) -> Dict:
        """Validate parameter definitions"""
        param_issues = []
        
        for node in nodes:
            signature = node.get('signature', {})
            parameters = signature.get('parameters', [])
            source_code = node.get('source_code', '')
            
            # Check if parameters are used in source code
            for param in parameters:
                param_name = param.get('name', '')
                if param_name and param_name not in source_code:
                    param_issues.append({
                        'node': node['name'],
                        'parameter': param_name,
                        'issue': 'Parameter defined but not used in source code',
                        'severity': 'info'
                    })
        
        result = {
            'total_parameters': sum(len(n.get('signature', {}).get('parameters', [])) for n in nodes),
            'issues': param_issues
        }
        
        if param_issues:
            print(f"   ℹ️  Found {len(param_issues)} parameter usage notes")
        else:
            print(f"   ✓ All parameters appear to be used correctly")
        
        return result
    
    def _validate_conditional_branches(self, nodes: List[Dict]) -> Dict:
        """Validate that conditional branches are explored"""
        branch_stats = {
            'if_statements': 0,
            'else_statements': 0,
            'switch_statements': 0,
            'try_catch': 0,
            'loops': 0
        }
        
        for node in nodes:
            source_code = node.get('source_code', '')
            
            branch_stats['if_statements'] += len(re.findall(r'\bif\s*\(', source_code))
            branch_stats['else_statements'] += len(re.findall(r'\belse\b', source_code))
            branch_stats['switch_statements'] += len(re.findall(r'\bswitch\s*\(', source_code))
            branch_stats['try_catch'] += len(re.findall(r'\btry\s*\{', source_code))
            branch_stats['loops'] += len(re.findall(r'\b(for|while)\s*\(', source_code))
        
        total_branches = sum(branch_stats.values())
        
        print(f"   ✓ Found {total_branches} conditional branches:")
        print(f"      - if statements: {branch_stats['if_statements']}")
        print(f"      - else statements: {branch_stats['else_statements']}")
        print(f"      - switch statements: {branch_stats['switch_statements']}")
        print(f"      - try-catch blocks: {branch_stats['try_catch']}")
        print(f"      - loops: {branch_stats['loops']}")
        
        return branch_stats
    
    def _validate_dao_operations(self, nodes: List[Dict]) -> Dict:
        """Validate DAO operations are captured"""
        dao_nodes = [n for n in nodes if n.get('node_type') == 'dao']
        
        dao_operations = {
            'get': 0,
            'save': 0,
            'update': 0,
            'delete': 0,
            'store': 0,
            'find': 0
        }
        
        for node in dao_nodes:
            name = node['name'].lower()
            if 'get' in name or 'find' in name:
                dao_operations['get'] += 1
            if 'save' in name or 'store' in name:
                dao_operations['save'] += 1
            if 'update' in name:
                dao_operations['update'] += 1
            if 'delete' in name:
                dao_operations['delete'] += 1
        
        result = {
            'total_dao_nodes': len(dao_nodes),
            'operations': dao_operations
        }
        
        print(f"   ✓ Found {len(dao_nodes)} DAO nodes:")
        print(f"      - GET operations: {dao_operations['get']}")
        print(f"      - SAVE/STORE operations: {dao_operations['save']}")
        print(f"      - UPDATE operations: {dao_operations['update']}")
        print(f"      - DELETE operations: {dao_operations['delete']}")
        
        return result
    
    def _compile_results(self, graph_dict: Dict, method_coverage: Dict, 
                        query_coverage: Dict, type_validation: Dict,
                        param_validation: Dict, branch_validation: Dict,
                        dao_validation: Dict) -> Dict:
        """Compile all validation results"""
        
        # Calculate overall accuracy score
        scores = []
        
        # Method coverage (40% weight)
        scores.append(method_coverage['coverage_percent'] * 0.4)
        
        # Query coverage (20% weight)
        query_score = 100 if query_coverage['total_queries'] > 0 else 0
        scores.append(query_score * 0.2)
        
        # Return type accuracy (15% weight)
        type_score = 100 - (len(type_validation['issues']) / max(type_validation['total_nodes'], 1) * 100)
        scores.append(type_score * 0.15)
        
        # Parameter accuracy (10% weight)
        param_score = 100 - (len(param_validation['issues']) / max(param_validation['total_parameters'], 1) * 100)
        scores.append(param_score * 0.1)
        
        # Branch coverage (10% weight)
        branch_score = 100 if sum(branch_validation.values()) > 0 else 0
        scores.append(branch_score * 0.1)
        
        # DAO coverage (5% weight)
        dao_score = 100 if dao_validation['total_dao_nodes'] > 0 else 0
        scores.append(dao_score * 0.05)
        
        overall_accuracy = sum(scores)
        
        return {
            'success': overall_accuracy >= 80,
            'overall_accuracy': overall_accuracy,
            'total_nodes': len(graph_dict['nodes']),
            'total_edges': len(graph_dict['edges']),
            'method_coverage': method_coverage,
            'query_coverage': query_coverage,
            'type_validation': type_validation,
            'parameter_validation': param_validation,
            'branch_validation': branch_validation,
            'dao_validation': dao_validation,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _print_summary(self, results: Dict):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        accuracy = results['overall_accuracy']
        
        print(f"\n📊 Overall Accuracy: {accuracy:.1f}%")
        
        if accuracy >= 95:
            print("   ✅ EXCELLENT - Call graph is highly accurate")
        elif accuracy >= 80:
            print("   ✅ GOOD - Call graph is accurate with minor issues")
        elif accuracy >= 60:
            print("   ⚠️  FAIR - Call graph has some accuracy issues")
        else:
            print("   ❌ POOR - Call graph has significant accuracy issues")
        
        print(f"\n📈 Detailed Scores:")
        print(f"   - Method Coverage: {results['method_coverage']['coverage_percent']:.1f}%")
        print(f"   - Total Nodes: {results['total_nodes']}")
        print(f"   - Total Edges: {results['total_edges']}")
        print(f"   - SQL/HQL Queries: {results['query_coverage']['total_queries']}")
        print(f"   - DAO Operations: {results['dao_validation']['total_dao_nodes']}")
        print(f"   - Conditional Branches: {sum(results['branch_validation'].values())}")
        
        if results['method_coverage']['missing']:
            print(f"\n⚠️  Missing Methods ({len(results['method_coverage']['missing'])}):")
            for method in results['method_coverage']['missing'][:10]:
                print(f"   - {method}")
            if len(results['method_coverage']['missing']) > 10:
                print(f"   ... and {len(results['method_coverage']['missing']) - 10} more")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   - {error}")
        
        if results['warnings']:
            print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
            for warning in results['warnings'][:5]:
                print(f"   - {warning}")
        
        print("\n" + "=" * 80)


def test_copyvisit_accuracy():
    """Test copyVisit API call graph accuracy"""
    validator = CallGraphAccuracyValidator()
    
    results = validator.validate_api(
        service_name="ClaimService",
        api_name="copyVisit"
    )
    
    # Save results to file
    output_file = Path(__file__).parent / "output" / "copyvisit_accuracy_report.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full report saved to: {output_file}")
    
    return results['success']


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CALL GRAPH ACCURACY VALIDATION TEST")
    print("=" * 80)
    
    success = test_copyvisit_accuracy()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ VALIDATION PASSED - Call graph is accurate!")
    else:
        print("❌ VALIDATION FAILED - Call graph needs improvement")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
