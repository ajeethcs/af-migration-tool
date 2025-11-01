# DTO/POJO Class Definition Extraction

## Problem

The call graph API was returning method signatures with return types (e.g., `ViewPatientOutput`), but **not the actual class definitions** showing what fields/attributes those types contain. This made it impossible to know the structure of return types and parameters.

## Solution

Added a new `DtoExtractor` module that:

1. **Collects all type names** used in method signatures (return types and parameters)
2. **Searches Java source files** for matching class definitions
3. **Parses class structure** using javalang to extract:
   - Package name
   - Fully qualified class name
   - All fields with their types, modifiers, and annotations
   - Inheritance (extends/implements)
   - Class-level modifiers and annotations

4. **Adds to metadata** as a new `dtos` section in the call graph

## Implementation

### New File: `core/dto_extractor.py`

```python
from core.dto_extractor import extract_dto_definitions

# Extract DTO definitions for specific types
dto_defs = extract_dto_definitions(
    java_source_paths=[ALLOFACTOR_SRC, ALLOFACTORSERVICE_SRC],
    type_names={'ViewPatientOutput', 'UserSession', 'ClaimCriteria'}
)
```

### Updated: `core/call_graph_builder.py`

The `CallGraphBuilder` now automatically:
1. Collects all type names from method signatures
2. Extracts their class definitions
3. Adds them to `metadata['dtos']`

## Call Graph Structure (Before vs After)

### Before
```json
{
  "nodes": [
    {
      "signature": {
        "return_type": "ViewPatientOutput",
        "parameters": [{"type": "UserSession"}, {"type": "int"}]
      }
    }
  ],
  "metadata": {
    "entities": {"Patient": {...}},
    "enums": {...}
  }
}
```

### After
```json
{
  "nodes": [
    {
      "signature": {
        "return_type": "ViewPatientOutput",
        "parameters": [{"type": "UserSession"}, {"type": "int"}]
      }
    }
  ],
  "metadata": {
    "entities": {"Patient": {...}},
    "enums": {...},
    "dtos": {
      "ViewPatientOutput": {
        "class_name": "ViewPatientOutput",
        "package": "com.iris.allofactor.services.output",
        "fully_qualified_name": "com.iris.allofactor.services.output.ViewPatientOutput",
        "fields": {
          "patient": {
            "type": "Patient",
            "modifiers": ["private"],
            "annotations": []
          },
          "blisError": {
            "type": "boolean",
            "modifiers": ["private"],
            "annotations": []
          },
          "errors": {
            "type": "List<ErrorMessage>",
            "modifiers": ["private"],
            "annotations": []
          }
        },
        "extends": "BaseOutput",
        "implements": [],
        "modifiers": ["public"],
        "annotations": []
      },
      "UserSession": {
        "class_name": "UserSession",
        "package": "com.iris.allofactor.common",
        "fields": {
          "iClinicId": {"type": "int", "modifiers": ["private"]},
          "iUserId": {"type": "int", "modifiers": ["private"]},
          "sUserName": {"type": "String", "modifiers": ["private"]}
        }
      }
    }
  }
}
```

## Usage

### For Frontend/Client

Now you can:

1. **Get return type name**: `node.signature.return_type` → `"ViewPatientOutput"`
2. **Get return type definition**: `metadata.dtos.ViewPatientOutput` → Full class structure
3. **Inspect fields**: `metadata.dtos.ViewPatientOutput.fields` → All attributes with types

### For LLM Code Conversion

The LLM now has complete type information to:
- Generate correct Python dataclasses/Pydantic models
- Understand data flow between methods
- Create accurate type hints
- Map Java types to Python equivalents

## Testing

Run the test script to verify DTO extraction:

```bash
python test_dto_extraction.py
```

This will:
1. Build a call graph for `viewPatientByPatientId`
2. Extract DTO definitions for all types used
3. Display the extracted DTOs
4. Save the full call graph to `output/call_graphs/test_dto_extraction.json`

## Notes

- **Primitive types** (int, boolean, etc.) are automatically skipped
- **Generic types** (List<T>, Map<K,V>) are handled correctly
- **Nested types** referenced in DTO fields are NOT automatically extracted (only top-level signature types)
- **Entity classes** from Hibernate mappings are in `metadata.entities`, not `metadata.dtos`
