"""
Helper Method Extractor

Extracts helper/utility method implementations that are called within
the main call graph but not traced as separate nodes.
"""
from pathlib import Path
from typing import Dict, List, Set
import re
from core.java_parser import JavaParser


class HelperMethodExtractor:
    """Extracts helper method implementations for business logic transparency"""
    
    def __init__(self):
        self.helper_methods: Dict[str, Dict] = {}
    
    def extract_helpers_from_class(self, file_path: Path, method_names: Set[str]) -> Dict[str, Dict]:
        """
        Extract specific helper methods from a Java class
        
        Args:
            file_path: Path to Java file
            method_names: Set of method names to extract
            
        Returns:
            Dictionary of method_name -> method_info
        """
        parser = JavaParser(file_path)
        all_methods = parser.get_methods()
        
        helpers = {}
        for method in all_methods:
            if method['name'] in method_names:
                helpers[method['name']] = {
                    'name': method['name'],
                    'signature': self._build_signature(method),
                    'source_code': method.get('source_code', ''),
                    'return_type': method.get('return_type', 'void'),
                    'parameters': method.get('parameters', []),
                    'file_path': str(file_path)
                }
        
        return helpers
    
    def _build_signature(self, method: Dict) -> str:
        """Build method signature string"""
        params = ', '.join([f"{p.get('type', 'Object')} {p.get('name', '')}" 
                           for p in method.get('parameters', [])])
        return f"{method.get('return_type', 'void')} {method['name']}({params})"
    
    def find_helper_calls_in_source(self, source_code: str) -> Set[str]:
        """
        Find all helper method calls in source code
        
        Args:
            source_code: Java source code
            
        Returns:
            Set of method names called
        """
        # Pattern: this.methodName( or ClassName.methodName(
        patterns = [
            r'this\.(\w+)\s*\(',           # this.method()
            r'(\w+)\s*\(',                  # method() - local calls
        ]
        
        method_calls = set()
        for pattern in patterns:
            matches = re.finditer(pattern, source_code)
            for match in matches:
                method_name = match.group(1)
                # Filter out common Java methods
                if method_name not in {'get', 'set', 'is', 'equals', 'toString', 
                                       'add', 'remove', 'size', 'length'}:
                    method_calls.add(method_name)
        
        return method_calls
    
    def extract_helpers_recursively(
        self, 
        file_path: Path, 
        entry_method_name: str,
        max_depth: int = 3
    ) -> Dict[str, Dict]:
        """
        Recursively extract helper methods called by entry method
        
        Args:
            file_path: Path to Java file
            entry_method_name: Starting method name
            max_depth: Maximum recursion depth
            
        Returns:
            Dictionary of all helper methods found
        """
        parser = JavaParser(file_path)
        all_methods = parser.get_methods()
        
        # Find entry method
        entry_method = None
        for method in all_methods:
            if method['name'] == entry_method_name:
                entry_method = method
                break
        
        if not entry_method:
            return {}
        
        helpers = {}
        visited = set()
        
        def extract_recursive(method_name: str, depth: int):
            if depth > max_depth or method_name in visited:
                return
            
            visited.add(method_name)
            
            # Find method
            method_info = None
            for m in all_methods:
                if m['name'] == method_name:
                    method_info = m
                    break
            
            if not method_info:
                return
            
            # Add to helpers
            helpers[method_name] = {
                'name': method_name,
                'signature': self._build_signature(method_info),
                'source_code': method_info.get('source_code', ''),
                'return_type': method_info.get('return_type', 'void'),
                'parameters': method_info.get('parameters', []),
                'file_path': str(file_path),
                'depth': depth
            }
            
            # Find calls in this method
            source = method_info.get('source_code', '')
            called_methods = self.find_helper_calls_in_source(source)
            
            # Recurse
            for called in called_methods:
                extract_recursive(called, depth + 1)
        
        # Start extraction
        extract_recursive(entry_method_name, 0)
        
        return helpers


def enhance_call_graph_with_helpers(call_graph: Dict, dao_file_path: Path) -> Dict:
    """
    Enhance call graph JSON with helper method implementations
    
    Args:
        call_graph: Existing call graph dictionary
        dao_file_path: Path to DAO implementation file
        
    Returns:
        Enhanced call graph with helpers section
    """
    extractor = HelperMethodExtractor()
    
    # Extract helpers for each DAO node
    all_helpers = {}
    
    for node in call_graph.get('nodes', []):
        if node.get('node_type') == 'dao':
            method_name = node.get('signature', {}).get('name', '')
            source_code = node.get('source_code', '')
            
            # Find helper calls
            helper_calls = extractor.find_helper_calls_in_source(source_code)
            
            if helper_calls:
                # Extract those helpers
                helpers = extractor.extract_helpers_from_class(
                    dao_file_path, 
                    helper_calls
                )
                all_helpers.update(helpers)
    
    # Add helpers to metadata
    if all_helpers:
        if 'metadata' not in call_graph:
            call_graph['metadata'] = {}
        call_graph['metadata']['helper_methods'] = all_helpers
    
    return call_graph


if __name__ == "__main__":
    # Test
    from config import ALLOFACTOR_SRC
    
    dao_file = ALLOFACTOR_SRC / "com" / "iris" / "allofactor" / "data" / "dao" / "hibernate" / "HibernateClaimDao.java"
    
    extractor = HelperMethodExtractor()
    helpers = extractor.extract_helpers_recursively(
        dao_file,
        "getMediumClaimByClaimCriteriaNew",
        max_depth=2
    )
    
    print(f"Found {len(helpers)} helper methods:")
    for name, info in helpers.items():
        print(f"  - {name} (depth: {info['depth']})")
