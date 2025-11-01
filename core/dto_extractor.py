"""
DTO/POJO Class Extractor

Extracts Java DTO, Output, Input, and POJO class definitions to provide
complete type information for method signatures in the call graph.
"""
from pathlib import Path
from typing import Dict, List, Optional, Set
import javalang
from dataclasses import dataclass, asdict


@dataclass
class FieldDefinition:
    """Represents a field in a DTO/POJO class"""
    name: str
    type: str
    modifiers: List[str]
    annotations: List[str] = None
    
    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []


@dataclass
class ClassDefinition:
    """Represents a complete DTO/POJO class definition"""
    class_name: str
    package: str
    fully_qualified_name: str
    fields: List[FieldDefinition]
    extends: Optional[str] = None
    implements: List[str] = None
    modifiers: List[str] = None
    annotations: List[str] = None
    
    def __post_init__(self):
        if self.implements is None:
            self.implements = []
        if self.modifiers is None:
            self.modifiers = []
        if self.annotations is None:
            self.annotations = []


class DtoExtractor:
    """Extracts DTO/POJO class definitions from Java source files"""
    
    def __init__(self):
        self.class_definitions: Dict[str, ClassDefinition] = {}
    
    def extract_from_paths(self, java_source_paths: List[Path], 
                          type_names: Set[str]) -> Dict[str, ClassDefinition]:
        """
        Extract class definitions for specific type names from Java source paths
        
        Args:
            java_source_paths: List of paths to search for Java files
            type_names: Set of class names to extract (e.g., {'ViewPatientOutput', 'UserSession'})
            
        Returns:
            Dictionary mapping fully qualified class names to ClassDefinition objects
        """
        self.class_definitions = {}
        
        # Search for each type name
        for type_name in type_names:
            # Skip primitive types
            if type_name in ['int', 'long', 'double', 'float', 'boolean', 'byte', 'char', 'short', 'void']:
                continue
            
            # Skip generic types (e.g., List<String>)
            if '<' in type_name or '>' in type_name:
                continue
            
            # Search in all source paths
            for source_path in java_source_paths:
                if not source_path.exists():
                    continue
                
                # Find the Java file
                java_files = list(source_path.rglob(f"{type_name}.java"))
                
                for java_file in java_files:
                    try:
                        class_def = self._parse_class_file(java_file)
                        if class_def:
                            self.class_definitions[class_def.fully_qualified_name] = class_def
                            # Also add by simple name for easier lookup
                            self.class_definitions[class_def.class_name] = class_def
                    except Exception as e:
                        print(f"Warning: Could not parse {java_file}: {e}")
        
        return self.class_definitions
    
    def _parse_class_file(self, java_file: Path) -> Optional[ClassDefinition]:
        """Parse a Java file and extract class definition"""
        try:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            # Parse the Java file
            tree = javalang.parse.parse(source_code)
            
            # Get package name
            package = tree.package.name if tree.package else ""
            
            # Find the main class declaration
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = node.name
                fully_qualified_name = f"{package}.{class_name}" if package else class_name
                
                # Extract fields
                fields = []
                for field_path, field_node in node.filter(javalang.tree.FieldDeclaration):
                    field_type = self._get_type_name(field_node.type)
                    modifiers = field_node.modifiers or []
                    annotations = [ann.name for ann in (field_node.annotations or [])]
                    
                    # Field declarations can have multiple declarators
                    for declarator in field_node.declarators:
                        fields.append(FieldDefinition(
                            name=declarator.name,
                            type=field_type,
                            modifiers=modifiers,
                            annotations=annotations
                        ))
                
                # Extract extends
                extends = None
                if node.extends:
                    extends = self._get_type_name(node.extends)
                
                # Extract implements
                implements = []
                if node.implements:
                    implements = [self._get_type_name(impl) for impl in node.implements]
                
                # Extract modifiers and annotations
                modifiers = node.modifiers or []
                annotations = [ann.name for ann in (node.annotations or [])]
                
                return ClassDefinition(
                    class_name=class_name,
                    package=package,
                    fully_qualified_name=fully_qualified_name,
                    fields=fields,
                    extends=extends,
                    implements=implements,
                    modifiers=modifiers,
                    annotations=annotations
                )
            
            return None
            
        except Exception as e:
            print(f"Error parsing {java_file}: {e}")
            return None
    
    def _get_type_name(self, type_node) -> str:
        """Get the string representation of a type"""
        if isinstance(type_node, javalang.tree.BasicType):
            return type_node.name
        elif isinstance(type_node, javalang.tree.ReferenceType):
            name = type_node.name
            if type_node.arguments:
                args = ", ".join([self._get_type_name(arg.type) if hasattr(arg, 'type') else str(arg) 
                                 for arg in type_node.arguments])
                return f"{name}<{args}>"
            return name
        elif hasattr(type_node, 'name'):
            return type_node.name
        return str(type_node)
    
    def to_dict(self) -> Dict[str, Dict]:
        """Convert class definitions to dictionary format"""
        result = {}
        for key, class_def in self.class_definitions.items():
            result[key] = {
                "class_name": class_def.class_name,
                "package": class_def.package,
                "fully_qualified_name": class_def.fully_qualified_name,
                "fields": {
                    field.name: {
                        "type": field.type,
                        "modifiers": field.modifiers,
                        "annotations": field.annotations
                    }
                    for field in class_def.fields
                },
                "extends": class_def.extends,
                "implements": class_def.implements,
                "modifiers": class_def.modifiers,
                "annotations": class_def.annotations
            }
        return result


def extract_dto_definitions(java_source_paths: List[Path], 
                            type_names: Set[str]) -> Dict[str, Dict]:
    """
    Convenience function to extract DTO definitions
    
    Args:
        java_source_paths: List of paths to search for Java files
        type_names: Set of class names to extract
        
    Returns:
        Dictionary of class definitions
    """
    extractor = DtoExtractor()
    extractor.extract_from_paths(java_source_paths, type_names)
    return extractor.to_dict()
