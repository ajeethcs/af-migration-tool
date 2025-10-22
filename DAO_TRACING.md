# DAO-Level Tracing Enhancement

## Overview

The call graph builder has been enhanced to trace method calls **beyond the DaoFacade** into the actual DAO implementation classes and their nested method calls.

## Problem Statement

Previously, the call graph would stop at the DaoFacade level:

```
ServiceImpl.getClaims()
  ↓
DaoFacadeImpl.getMediumClaimBO()
  ↓
[STOPPED HERE]
```

But the DaoFacade methods typically delegate to DAO implementations:

```java
// DaoFacadeImpl.java
public MediumClaimBO getMediumClaimBO(ClaimCriteria claimCriteria,
        int iOffset, int iCount, int iClinicID) throws DataAccessException {
    return this.mediumClaimBODao.getMediumClaimBO(claimCriteria, iOffset,
            iCount, iClinicID);
}
```

We needed to trace into `MediumClaimBODaoImpl.getMediumClaimBO()` and any methods it calls.

## Solution

### Enhanced Pattern Recognition

The call graph builder now recognizes three types of DAO method calls:

#### 1. DAO Field Calls
```java
this.mediumClaimBODao.getMediumClaimBO(...)
```
Pattern: `this\.(\w+Dao)\.(\w+)\s*\(`

#### 2. Direct DAO Calls
```java
claimDao.getMediumClaimByClaimCriteria(...)
```
Pattern: `(?<!this\.)\b(\w+Dao)\.(\w+)\s*\(`

#### 3. Existing Patterns (unchanged)
- Facade calls: `daoFacade.method()`
- Helper calls: `HelperClass.method()`
- Internal calls: `this.method()`

### DAO Resolution Process

When a DAO method call is detected:

1. **Extract DAO field name** (e.g., `mediumClaimBODao`)

2. **Resolve DAO class name**:
   - First, check the class fields to find the actual type
   - If not found, use naming convention: `mediumClaimBODao` → `MediumClaimBODaoImpl`

3. **Locate DAO implementation file**:
   - Look in: `allofactor/src/com/iris/allofactor/data/dao/impl/`
   - Try: `MediumClaimBODaoImpl.java`
   - Fallback: `MediumClaimBODao.java`

4. **Parse and extract method**:
   - Parse the DAO implementation file
   - Find the matching method
   - Extract its source code

5. **Recursively trace**:
   - Analyze the DAO method's source code
   - Find any nested method calls (other DAOs, helpers, etc.)
   - Continue tracing until depth limit

## Example Trace

### Input API
```java
// ClaimServiceImpl.getClaims()
```

### Complete Call Graph

```
Node 1: getClaims (service_impl)
  ├─ ClaimServiceImpl.getClaims()
  └─ Calls: daoFacade.getMediumClaimBO()
      ↓
Node 2: getMediumClaimBO (facade)
  ├─ DaoFacadeImpl.getMediumClaimBO()
  └─ Calls: this.mediumClaimBODao.getMediumClaimBO()
      ↓
Node 3: getMediumClaimBO (dao) ← NEW!
  ├─ MediumClaimBODaoImpl.getMediumClaimBO()
  └─ Calls:
      ├─ claimDao.getMediumClaimByClaimCriteriaNew()
      └─ claimDao.getCoutMediumClaimByClaimCriteriaNew()
          ↓
Node 4: getMediumClaimByClaimCriteriaNew (dao) ← NEW!
  ├─ ClaimDao.getMediumClaimByClaimCriteriaNew()
  └─ Hibernate query execution
      ↓
Node 5: getCoutMediumClaimByClaimCriteriaNew (dao) ← NEW!
  ├─ ClaimDao.getCoutMediumClaimByClaimCriteriaNew()
  └─ Hibernate count query
```

## Code Changes

### 1. Enhanced `_extract_method_calls()`

Added patterns for DAO field and direct calls:

```python
# Pattern for DAO field calls (e.g., this.mediumClaimBODao.method())
dao_field_pattern = r'this\.(\w+Dao)\.(\w+)\s*\('
for match in re.finditer(dao_field_pattern, source_code):
    method_calls.append({
        "object": match.group(1),
        "method": match.group(2),
        "type": "dao_field"
    })

# Pattern for direct DAO calls (e.g., claimDao.method())
dao_direct_pattern = r'(?<!this\.)\b(\w+Dao)\.(\w+)\s*\('
for match in re.finditer(dao_direct_pattern, source_code):
    method_calls.append({
        "object": match.group(1),
        "method": match.group(2),
        "type": "dao_direct"
    })
```

### 2. Enhanced `_resolve_method_call()`

Added handling for DAO calls:

```python
if call_type == "facade":
    return self._find_facade_method(method_name)
elif call_type == "dao_field" or call_type == "dao_direct":
    return self._find_dao_method(call_info["object"], method_name, current_parser)
elif call_type == "helper":
    return self._find_helper_method(call_info["object"], method_name)
```

### 3. New `_find_dao_method()`

Locates and parses DAO implementation methods:

```python
def _find_dao_method(self, dao_field: str, method_name: str, 
                     current_parser: JavaParser) -> Optional[Dict]:
    """Find a method in a DAO implementation"""
    # Resolve DAO class name from field
    dao_class_name = self._resolve_dao_class(dao_field, current_parser)
    
    if not dao_class_name:
        # Use naming convention
        dao_class_name = dao_field[0].upper() + dao_field[1:] + "Impl"
    
    # Locate DAO implementation file
    dao_impl_file = DAO_PATH / "impl" / f"{dao_class_name}.java"
    
    # Parse and find method
    parser = JavaParser(dao_impl_file)
    methods = parser.get_methods()
    
    for method in methods:
        if method["name"] == method_name:
            return {
                "method_info": method,
                "parser": parser,
                "node_type": NodeType.DAO
            }
```

### 4. New `_resolve_dao_class()`

Resolves the actual DAO class from a field name:

```python
def _resolve_dao_class(self, dao_field: str, parser: JavaParser) -> Optional[str]:
    """Resolve the actual DAO class name from a field name"""
    fields = parser.get_fields()
    
    for field in fields:
        if field["name"] == dao_field:
            field_type = field["type"]
            # Handle generic types
            if "<" in field_type:
                field_type = field_type.split("<")[0]
            return field_type
    
    return None
```

### 5. New `_determine_node_type()`

Automatically determines node type from class name:

```python
def _determine_node_type(self, parser: JavaParser) -> NodeType:
    """Determine the node type based on the class name"""
    class_name = parser.get_fully_qualified_name()
    
    if "ServiceImpl" in class_name:
        return NodeType.SERVICE_IMPL
    elif "DaoFacadeImpl" in class_name or "DaoFacade" in class_name:
        return NodeType.FACADE
    elif "DaoImpl" in class_name or "Dao" in class_name:
        return NodeType.DAO
    elif "Helper" in class_name:
        return NodeType.HELPER
    else:
        return NodeType.UTILITY
```

## Testing

### Run the DAO Tracing Test

```bash
python test_dao_tracing.py
```

This will:
1. Build a call graph for an API that uses DAOs
2. Verify that DAO nodes are present
3. Display the complete call chain
4. Save the graph to `output/call_graphs/test_dao_tracing.json`

### Expected Output

```
TEST: DAO-Level Tracing
============================================================

Building call graph for ClaimService.getClaims...
This should trace through:
  1. ServiceImpl method
  2. DaoFacade method
  3. DAO implementation method (e.g., MediumClaimBODaoImpl)
  4. Any methods called within the DAO

✓ Call graph generated successfully!
  - Total nodes: 12
  - Total edges: 15

  Node breakdown:
    - service_impl: 1
    - facade: 1
    - dao: 8
    - helper: 2

✓ SUCCESS: Found 8 DAO node(s)!

  DAO nodes found:
    - getMediumClaimBO in com.iris.allofactor.data.dao.impl.MediumClaimBODaoImpl
      File: .../MediumClaimBODaoImpl.java
      Dependencies: 2 method(s)
    - getMediumClaimByClaimCriteriaNew in com.iris.allofactor.data.dao.ClaimDao
      ...
```

## Benefits

### 1. Complete Code Understanding
- See the entire execution path from API to database
- Understand all data access patterns
- Identify complex query logic

### 2. Better Migration Planning
- Know exactly what database operations are performed
- Identify Hibernate queries that need conversion
- Understand transaction boundaries

### 3. Accurate Code Conversion
- LLM has complete context for conversion
- Can map Hibernate queries to SQLAlchemy
- Preserve business logic accurately

### 4. Dependency Analysis
- See all DAO dependencies
- Identify shared DAOs across APIs
- Plan migration order based on dependencies

## JSON Output Example

```json
{
  "api_name": "getClaims",
  "service_name": "ClaimService",
  "entry_point": "node_1",
  "nodes": [
    {
      "id": "node_1",
      "name": "getClaims",
      "node_type": "service_impl",
      "dependencies": ["node_2"]
    },
    {
      "id": "node_2",
      "name": "getMediumClaimBO",
      "node_type": "facade",
      "dependencies": ["node_3"]
    },
    {
      "id": "node_3",
      "name": "getMediumClaimBO",
      "class_name": "com.iris.allofactor.data.dao.impl.MediumClaimBODaoImpl",
      "node_type": "dao",
      "source_code": "public MediumClaimBO getMediumClaimBO(...) { ... }",
      "dependencies": ["node_4", "node_5"]
    },
    {
      "id": "node_4",
      "name": "getMediumClaimByClaimCriteriaNew",
      "node_type": "dao",
      "dependencies": []
    },
    {
      "id": "node_5",
      "name": "getCoutMediumClaimByClaimCriteriaNew",
      "node_type": "dao",
      "dependencies": []
    }
  ],
  "edges": [
    {"source": "node_1", "target": "node_2", "call_type": "facade"},
    {"source": "node_2", "target": "node_3", "call_type": "dao_field"},
    {"source": "node_3", "target": "node_4", "call_type": "dao_direct"},
    {"source": "node_3", "target": "node_5", "call_type": "dao_direct"}
  ]
}
```

## Limitations & Future Enhancements

### Current Limitations
1. **Depth limit**: Set to 100 nodes to prevent infinite recursion
2. **Pattern matching**: May miss some complex call patterns
3. **Dynamic calls**: Cannot trace reflection or dynamic method calls
4. **Hibernate queries**: Extracted as strings, not parsed

### Future Enhancements
1. **Hibernate query parsing**: Extract and analyze HQL/SQL queries
2. **Entity relationship mapping**: Build entity dependency graphs
3. **Transaction analysis**: Identify transaction boundaries
4. **Performance analysis**: Estimate query complexity
5. **Database schema extraction**: Map entities to tables

## Configuration

The DAO path is configured in `config.py`:

```python
# Facade and DAO paths
FACADE_PATH = ALLOFACTOR_SRC / "data" / "dao" / "facade"
DAO_PATH = ALLOFACTOR_SRC / "data" / "dao"
```

DAO implementations are expected in:
```
allofactor/src/com/iris/allofactor/data/dao/impl/
```

## Troubleshooting

### Issue: DAO nodes not appearing in graph

**Possible causes:**
1. DAO naming doesn't follow convention (e.g., not ending in "Dao")
2. DAO implementation file not in expected location
3. Pattern matching not capturing the call

**Solutions:**
1. Check the DAO field name in the facade
2. Verify the DAO implementation file exists
3. Add debug logging to see what patterns are matched

### Issue: Incomplete DAO method source

**Possible causes:**
1. Method has complex brace nesting
2. Method is very large
3. Parsing error

**Solutions:**
1. Check the source file manually
2. Adjust the method extraction logic in JavaParser
3. Increase MAX_METHOD_SIZE in config

## Summary

The enhanced DAO tracing provides complete visibility into the data access layer, enabling:
- ✅ Full API execution path analysis
- ✅ Complete code context for migration
- ✅ Accurate dependency mapping
- ✅ Better migration planning

This makes the migration tool significantly more powerful for understanding and migrating complex business logic.
