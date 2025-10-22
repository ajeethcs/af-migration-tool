"""
Schema and Hibernate Mapping Extractor

Extracts database schema information from Hibernate mapping files (.hbm.xml)
and Java enum classes to provide complete metadata for LLM conversion.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import re
from dataclasses import dataclass, asdict


@dataclass
class FieldMapping:
    """Represents a field-to-column mapping"""
    java_field: str
    column_name: str
    java_type: Optional[str] = None
    nullable: bool = True
    insert: bool = True
    update: bool = True


@dataclass
class EntityMapping:
    """Represents a complete entity mapping"""
    java_class: str
    table_name: str
    primary_key: Optional[FieldMapping] = None
    fields: List[FieldMapping] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []


class SchemaExtractor:
    """Extracts schema information from Hibernate mappings"""
    
    def __init__(self, hibernate_maps_path: Path):
        """
        Initialize the schema extractor
        
        Args:
            hibernate_maps_path: Path to directory containing .hbm.xml files
        """
        self.hibernate_maps_path = Path(hibernate_maps_path)
        self.entity_mappings: Dict[str, EntityMapping] = {}
        
    def extract_all_mappings(self) -> Dict[str, EntityMapping]:
        """
        Extract all entity mappings from .hbm.xml files
        
        Returns:
            Dictionary mapping entity class names to EntityMapping objects
        """
        if not self.hibernate_maps_path.exists():
            print(f"Warning: Hibernate maps path does not exist: {self.hibernate_maps_path}")
            return {}
        
        hbm_files = list(self.hibernate_maps_path.glob("*.hbm.xml"))
        print(f"Found {len(hbm_files)} Hibernate mapping files")
        
        for hbm_file in hbm_files:
            try:
                self._parse_hbm_file(hbm_file)
            except Exception as e:
                print(f"Error parsing {hbm_file.name}: {e}")
        
        print(f"Extracted {len(self.entity_mappings)} entity mappings")
        return self.entity_mappings
    
    def _parse_hbm_file(self, hbm_file: Path):
        """Parse a single .hbm.xml file"""
        try:
            tree = ET.parse(hbm_file)
            root = tree.getroot()
            
            # Find all class definitions in the file
            for class_elem in root.findall('.//class'):
                entity_mapping = self._parse_class_element(class_elem)
                if entity_mapping:
                    # Use simple class name as key
                    class_name = entity_mapping.java_class.split('.')[-1]
                    self.entity_mappings[class_name] = entity_mapping
                    
        except ET.ParseError as e:
            print(f"XML parse error in {hbm_file.name}: {e}")
    
    def _parse_class_element(self, class_elem: ET.Element) -> Optional[EntityMapping]:
        """Parse a <class> element from Hibernate mapping"""
        java_class = class_elem.get('name')
        table_name = class_elem.get('table')
        
        if not java_class or not table_name:
            return None
        
        entity_mapping = EntityMapping(
            java_class=java_class,
            table_name=table_name,
            fields=[]
        )
        
        # Parse primary key (id element)
        id_elem = class_elem.find('id')
        if id_elem is not None:
            pk_field = FieldMapping(
                java_field=id_elem.get('name', ''),
                column_name=id_elem.get('column', ''),
                nullable=False
            )
            entity_mapping.primary_key = pk_field
        
        # Parse regular properties
        for prop_elem in class_elem.findall('property'):
            field_mapping = self._parse_property_element(prop_elem)
            if field_mapping:
                entity_mapping.fields.append(field_mapping)
        
        return entity_mapping
    
    def _parse_property_element(self, prop_elem: ET.Element) -> Optional[FieldMapping]:
        """Parse a <property> element"""
        java_field = prop_elem.get('name')
        column_name = prop_elem.get('column')
        
        if not java_field or not column_name:
            return None
        
        # Parse optional attributes
        insert = prop_elem.get('insert', 'true').lower() == 'true'
        update = prop_elem.get('update', 'true').lower() == 'true'
        not_null = prop_elem.get('not-null', 'false').lower() == 'true'
        
        return FieldMapping(
            java_field=java_field,
            column_name=column_name,
            nullable=not not_null,
            insert=insert,
            update=update
        )
    
    def get_mapping_for_entity(self, entity_name: str) -> Optional[EntityMapping]:
        """
        Get mapping for a specific entity
        
        Args:
            entity_name: Simple class name (e.g., "MediumClaim")
            
        Returns:
            EntityMapping or None if not found
        """
        return self.entity_mappings.get(entity_name)
    
    def get_field_mapping(self, entity_name: str, java_field: str) -> Optional[str]:
        """
        Get database column name for a Java field
        
        Args:
            entity_name: Simple class name
            java_field: Java field name
            
        Returns:
            Column name or None if not found
        """
        entity = self.get_mapping_for_entity(entity_name)
        if not entity:
            return None
        
        # Check primary key
        if entity.primary_key and entity.primary_key.java_field == java_field:
            return entity.primary_key.column_name
        
        # Check regular fields
        for field in entity.fields:
            if field.java_field == java_field:
                return field.column_name
        
        return None
    
    def to_dict(self) -> Dict:
        """Convert all mappings to dictionary format for JSON export"""
        result = {}
        for entity_name, mapping in self.entity_mappings.items():
            entity_dict = {
                "java_class": mapping.java_class,
                "table_name": mapping.table_name,
                "primary_key": None,
                "fields": {}
            }
            
            # Add primary key
            if mapping.primary_key:
                entity_dict["primary_key"] = {
                    "java_field": mapping.primary_key.java_field,
                    "column": mapping.primary_key.column_name
                }
            
            # Add fields
            for field in mapping.fields:
                entity_dict["fields"][field.java_field] = {
                    "column": field.column_name,
                    "nullable": field.nullable,
                    "insert": field.insert,
                    "update": field.update
                }
            
            result[entity_name] = entity_dict
        
        return result


class EnumExtractor:
    """Extracts enum definitions from Java source files"""
    
    def __init__(self, java_source_paths: List[Path]):
        """
        Initialize enum extractor
        
        Args:
            java_source_paths: List of paths to search for Java enum files
        """
        self.java_source_paths = [Path(p) for p in java_source_paths]
        self.enum_definitions: Dict[str, Dict[str, int]] = {}
    
    def extract_all_enums(self) -> Dict[str, Dict[str, int]]:
        """
        Extract all enum definitions
        
        Returns:
            Dictionary mapping enum class names to their constant values
        """
        for source_path in self.java_source_paths:
            if not source_path.exists():
                continue
            
            # Find all Java files
            java_files = list(source_path.rglob("*.java"))
            
            for java_file in java_files:
                try:
                    self._parse_java_file(java_file)
                except Exception as e:
                    pass  # Skip files that can't be parsed
        
        print(f"Extracted {len(self.enum_definitions)} enum definitions")
        return self.enum_definitions
    
    def _parse_java_file(self, java_file: Path):
        """Parse a Java file looking for enum definitions"""
        try:
            content = java_file.read_text(encoding='utf-8', errors='ignore')
            
            # Look for enum class definitions
            enum_pattern = r'public\s+enum\s+(\w+)\s*\{'
            enum_matches = re.finditer(enum_pattern, content)
            
            for match in enum_matches:
                enum_name = match.group(1)
                enum_values = self._extract_enum_values(content, match.start())
                
                if enum_values:
                    self.enum_definitions[enum_name] = enum_values
                    
        except Exception:
            pass  # Skip problematic files
    
    def _extract_enum_values(self, content: str, start_pos: int) -> Dict[str, int]:
        """Extract enum constant values from enum definition"""
        enum_values = {}
        
        # Find the enum body
        brace_start = content.find('{', start_pos)
        if brace_start == -1:
            return enum_values
        
        # Find matching closing brace
        brace_count = 1
        pos = brace_start + 1
        enum_body = ""
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            if brace_count > 0:
                enum_body += content[pos]
            pos += 1
        
        # Parse enum constants with values - multiple patterns
        patterns = [
            r'(\w+)\s*\(\s*(\d+)\s*\)',           # CONSTANT(123)
            r'(\w+)\s*\(\s*"[^"]*"\s*,\s*(\d+)\s*\)',  # CONSTANT("name", 123)
            r'(\w+)\s*=\s*(\d+)',                  # CONSTANT = 123
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, enum_body):
                constant_name = match.group(1)
                constant_value = int(match.group(2))
                # Don't overwrite if already found
                if constant_name not in enum_values:
                    enum_values[constant_name] = constant_value
        
        return enum_values
    
    def to_dict(self) -> Dict:
        """Convert enum definitions to dictionary for JSON export"""
        return self.enum_definitions


def extract_metadata(
    hibernate_maps_path: Path,
    java_source_paths: List[Path]
) -> Dict:
    """
    Extract complete metadata including entity mappings and enums
    
    Args:
        hibernate_maps_path: Path to Hibernate mapping files
        java_source_paths: Paths to Java source directories
        
    Returns:
        Complete metadata dictionary
    """
    print("\n" + "="*60)
    print("Extracting Schema Metadata")
    print("="*60)
    
    # Extract entity mappings
    print("\n1. Extracting Hibernate entity mappings...")
    schema_extractor = SchemaExtractor(hibernate_maps_path)
    entity_mappings = schema_extractor.extract_all_mappings()
    
    # Extract enums
    print("\n2. Extracting enum definitions...")
    enum_extractor = EnumExtractor(java_source_paths)
    enum_definitions = enum_extractor.extract_all_enums()
    
    # Combine into metadata
    metadata = {
        "entities": schema_extractor.to_dict(),
        "enums": enum_extractor.to_dict(),
        "database": {
            "dialect": "mysql",  # Can be detected from hibernate config
            "version": "5.7"
        }
    }
    
    print("\n" + "="*60)
    print(f"Metadata extraction complete!")
    print(f"  - Entities: {len(entity_mappings)}")
    print(f"  - Enums: {len(enum_definitions)}")
    print("="*60)
    
    return metadata


if __name__ == "__main__":
    # Test the extractor
    from config import ALLOFACTOR_SRC, ALLOFACTORSERVICE_SRC
    
    hibernate_maps = ALLOFACTOR_SRC / "com" / "iris" / "allofactor" / "data" / "dao" / "hibernate" / "maps"
    
    metadata = extract_metadata(
        hibernate_maps_path=hibernate_maps,
        java_source_paths=[ALLOFACTOR_SRC, ALLOFACTORSERVICE_SRC]
    )
    
    # Print sample
    if "MediumClaim" in metadata["entities"]:
        print("\nSample: MediumClaim entity mapping:")
        import json
        print(json.dumps(metadata["entities"]["MediumClaim"], indent=2))
