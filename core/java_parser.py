"""
Java source code parser using javalang
"""
import javalang
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

class JavaParser:
    """Parser for Java source files"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.source_code = self._read_file()
        self.tree = None
        self.package_name = None
        self.class_name = None
        self._parse()
    
    def _read_file(self) -> str:
        """Read the Java source file"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _parse(self):
        """Parse the Java source code"""
        try:
            self.tree = javalang.parse.parse(self.source_code)
            self.package_name = self.tree.package.name if self.tree.package else ""
            
            # Get the main class name
            for path, node in self.tree.filter(javalang.tree.ClassDeclaration):
                self.class_name = node.name
                break
        except Exception as e:
            print(f"Error parsing {self.file_path}: {e}")
            self.tree = None
    
    def get_fully_qualified_name(self) -> str:
        """Get the fully qualified class name"""
        if self.package_name and self.class_name:
            return f"{self.package_name}.{self.class_name}"
        return self.class_name or ""
    
    def get_methods(self) -> List[Dict]:
        """Extract all methods from the class"""
        if not self.tree:
            return []
        
        methods = []
        for path, node in self.tree.filter(javalang.tree.MethodDeclaration):
            method_info = self._extract_method_info(node, path)
            if method_info:
                methods.append(method_info)
        
        return methods
    
    def _extract_method_info(self, node: javalang.tree.MethodDeclaration, path) -> Optional[Dict]:
        """Extract detailed information about a method"""
        try:
            # Get method signature
            method_name = node.name
            return_type = self._get_type_name(node.return_type) if node.return_type else "void"
            
            # Get parameters
            parameters = []
            if node.parameters:
                for param in node.parameters:
                    param_type = self._get_type_name(param.type)
                    parameters.append({
                        "name": param.name,
                        "type": param_type,
                        "annotations": [ann.name for ann in (param.annotations or [])]
                    })
            
            # Get modifiers
            modifiers = node.modifiers or []
            
            # Get annotations
            annotations = [ann.name for ann in (node.annotations or [])]
            
            # Get throws
            throws = [self._get_type_name(t) for t in (node.throws or [])]
            
            # Get source code
            source_code = self._extract_method_source(method_name, node)
            
            # Get line number
            line_number = node.position.line if node.position else 0
            
            return {
                "name": method_name,
                "return_type": return_type,
                "parameters": parameters,
                "modifiers": modifiers,
                "annotations": annotations,
                "throws": throws,
                "source_code": source_code,
                "line_number": line_number,
                "class_name": self.get_fully_qualified_name()
            }
        except Exception as e:
            print(f"Error extracting method info: {e}")
            return None
    
    def _get_type_name(self, type_node) -> str:
        """Get the string representation of a type"""
        if isinstance(type_node, javalang.tree.BasicType):
            return type_node.name
        elif isinstance(type_node, javalang.tree.ReferenceType):
            name = type_node.name
            if type_node.arguments:
                args = ", ".join([self._get_type_name(arg.type) for arg in type_node.arguments])
                return f"{name}<{args}>"
            return name
        elif hasattr(type_node, 'name'):
            return type_node.name
        return str(type_node)
    
    def _extract_method_source(self, method_name: str, node: javalang.tree.MethodDeclaration) -> str:
        """Extract the source code of a method"""
        try:
            if not node.position:
                print(f"Warning: No position info for method {method_name}")
                return ""
            
            lines = self.source_code.split('\n')
            start_line = node.position.line - 1
            
            if start_line >= len(lines):
                print(f"Warning: Start line {start_line} out of range for method {method_name}")
                return ""
            
            # Find the method end by counting braces
            brace_count = 0
            in_method = False
            end_line = start_line
            
            for i in range(start_line, len(lines)):
                line = lines[i]
                
                # Count opening and closing braces
                for char in line:
                    if char == '{':
                        brace_count += 1
                        in_method = True
                    elif char == '}':
                        brace_count -= 1
                        if in_method and brace_count == 0:
                            end_line = i
                            break
                
                if in_method and brace_count == 0:
                    break
            
            # If we never found the closing brace, something went wrong
            if in_method and brace_count != 0:
                print(f"Warning: Unclosed braces for method {method_name}, brace_count={brace_count}")
                # Try to extract at least some lines
                end_line = min(start_line + 50, len(lines) - 1)
            
            # Extract the method source
            method_source = '\n'.join(lines[start_line:end_line + 1])
            
            # Debug: Print first line to verify extraction
            if method_source:
                first_line = method_source.split('\n')[0][:80]
                # Uncomment for debugging:
                # print(f"Debug: Extracted method {method_name}: {first_line}...")
            
            return method_source
        except Exception as e:
            print(f"Error extracting method source for {method_name}: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def find_method_calls(self, method_source: str) -> List[str]:
        """Find all method calls within a method"""
        if not method_source:
            return []
        
        method_calls = []
        
        # Pattern to match method calls
        # This is a simplified pattern and may need refinement
        pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(pattern, method_source)
        
        for match in matches:
            object_name = match.group(1)
            method_name = match.group(2)
            method_calls.append(f"{object_name}.{method_name}")
        
        # Also find direct method calls (without object)
        pattern = r'(?<![.\w])(\w+)\s*\('
        matches = re.finditer(pattern, method_source)
        
        for match in matches:
            method_name = match.group(1)
            # Filter out common keywords
            if method_name not in ['if', 'for', 'while', 'switch', 'catch', 'return', 'new']:
                method_calls.append(method_name)
        
        return list(set(method_calls))
    
    def get_imports(self) -> List[str]:
        """Get all imports from the file"""
        if not self.tree:
            return []
        
        imports = []
        for imp in self.tree.imports:
            imports.append(imp.path)
        
        return imports
    
    def get_fields(self) -> List[Dict]:
        """Get all fields/member variables"""
        if not self.tree:
            return []
        
        fields = []
        for path, node in self.tree.filter(javalang.tree.FieldDeclaration):
            field_type = self._get_type_name(node.type)
            for declarator in node.declarators:
                fields.append({
                    "name": declarator.name,
                    "type": field_type,
                    "modifiers": node.modifiers or []
                })
        
        return fields
