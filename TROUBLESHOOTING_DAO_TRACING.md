# Troubleshooting DAO Tracing

## Issue Summary

When running `test_dao_tracing.py`, the call graph is generated but **no DAO nodes are found**, even though the facade method clearly contains DAO calls.

## Investigation Results

### ✅ What's Working

1. **Pattern Matching**: The regex patterns work correctly (verified with `test_pattern_matching.py`)
   - `this\.(\w+Dao)\.(\w+)\s*\(` correctly matches `this.mediumClaimBODao.getMediumClaimBO(`

2. **Source Code Extraction**: The facade method source is being extracted correctly
   - From `test_dao_tracing.json`: The facade node contains the full source code including `this.mediumClaimBODao.getMediumClaimBO`

3. **Call Graph Structure**: The basic call graph is working
   - ServiceImpl → Facade ✅
   - ServiceImpl → Helper ✅

### ❌ What's Not Working

The facade node has **empty dependencies** (`"dependencies": []`), meaning `_extract_method_calls()` is not finding the DAO call in the facade method source code.

## Root Cause Analysis

Looking at the JSON output:

```json
{
  "id": "com.iris.allofactor.data.dao.facade.DaoFacadeImpl.getMediumClaimBO_9375fc35",
  "name": "getMediumClaimBO",
  "node_type": "facade",
  "source_code": "\tpublic MediumClaimBO getMediumClaimBO(ClaimCriteria claimCriteria,\n\t\t\tint iOffset, int iCount, int iClinicID) throws DataAccessException {\n\t\treturn this.mediumClaimBODao.getMediumClaimBO(claimCriteria, iOffset,\n\t\t\t\tiCount, iClinicID);\n\t}",
  "dependencies": []  // ← EMPTY!
}
```

The source code **contains** `this.mediumClaimBODao.getMediumClaimBO` but dependencies are empty.

## Possible Causes

### 1. The `_trace_method_calls()` is not being called for facade nodes

Check if there's a condition preventing recursive tracing for facade nodes.

### 2. The depth limit is being reached too early

Current limit is 100 visited methods. Check if we're hitting this limit.

### 3. The pattern matching is failing on the actual source

The source code has tabs (`\t`) which might affect matching.

### 4. The `_resolve_method_call()` is failing to find the DAO method

Even if the pattern matches, the resolution might be failing.

## Debug Steps

### Step 1: Enable Debug Output

Run with debug enabled:

```bash
# Set environment variable
export DEBUG_CALL_GRAPH=1  # Linux/Mac
set DEBUG_CALL_GRAPH=1     # Windows CMD
$env:DEBUG_CALL_GRAPH="1"  # Windows PowerShell

# Run test
python test_with_debug.py
```

This will print:
- `[DEBUG] Found facade call: daoFacade.method()`
- `[DEBUG] Found DAO field call: this.daoName.method()`

### Step 2: Check Pattern Matching

The pattern should match despite tabs:

```python
import re

source = "\treturn this.mediumClaimBODao.getMediumClaimBO(claimCriteria, iOffset,\n\t\t\t\tiCount, iClinicID);"
pattern = r'this\.(\w+Dao)\.(\w+)\s*\('

matches = list(re.finditer(pattern, source))
print(f"Matches: {len(matches)}")  # Should be 1
for match in matches:
    print(f"  {match.group(1)}.{match.group(2)}")  # Should print: mediumClaimBODao.getMediumClaimBO
```

### Step 3: Check if `_trace_method_calls()` is being called

Add print statement in `_trace_method_calls()`:

```python
def _trace_method_calls(self, method_info: Dict, source_node_id: str, parser: JavaParser):
    """Recursively trace method calls"""
    source_code = method_info.get("source_code", "")
    
    print(f"[TRACE] Tracing calls in {method_info['name']}, source length: {len(source_code)}")
    
    if not source_code:
        print(f"[TRACE] No source code for {method_info['name']}")
        return
    ...
```

### Step 4: Check DAO Resolution

Add print in `_find_dao_method()`:

```python
def _find_dao_method(self, dao_field: str, method_name: str, current_parser: JavaParser):
    print(f"[DAO RESOLVE] Looking for {dao_field}.{method_name}")
    
    dao_class_name = self._resolve_dao_class(dao_field, current_parser)
    print(f"[DAO RESOLVE] Resolved to class: {dao_class_name}")
    
    dao_impl_file = DAO_PATH / "impl" / f"{dao_class_name}.java"
    print(f"[DAO RESOLVE] Looking for file: {dao_impl_file}")
    print(f"[DAO RESOLVE] File exists: {dao_impl_file.exists()}")
    ...
```

## Quick Fix to Test

To quickly test if the issue is in the tracing logic, manually check:

```python
from core.call_graph_builder import CallGraphBuilder

builder = CallGraphBuilder()

# Test pattern matching directly
source = "\treturn this.mediumClaimBODao.getMediumClaimBO(claimCriteria, iOffset,\n\t\t\t\tiCount, iClinicID);"
calls = builder._extract_method_calls(source)

print(f"Found {len(calls)} calls:")
for call in calls:
    print(f"  {call}")
```

Expected output:
```
Found 1 calls:
  {'object': 'mediumClaimBODao', 'method': 'getMediumClaimBO', 'type': 'dao_field'}
```

## Solution Approaches

### If Pattern Matching Fails:
- Adjust regex to handle tabs/whitespace better
- Use `\s+` instead of `\s*` in some places
- Add more flexible patterns

### If Resolution Fails:
- Check DAO_PATH configuration
- Verify file naming conventions
- Add fallback resolution strategies

### If Tracing Doesn't Happen:
- Check depth limit
- Verify `_trace_method_calls()` is called for all node types
- Check for early returns in the tracing logic

## Testing Commands

```bash
# 1. Test pattern matching
python test_pattern_matching.py

# 2. Test with debug output
python test_with_debug.py

# 3. Full DAO tracing test
python test_dao_tracing.py

# 4. Check generated JSON
cat output/call_graphs/test_dao_tracing.json | grep -A 20 "getMediumClaimBO"
```

## Expected vs Actual

### Expected Call Graph:
```
getClaims (service_impl)
  ├─ getMediumClaimBO (facade)
  │   └─ getMediumClaimBO (dao) ← MISSING!
  └─ populateGetClaimsOutPut (helper)
```

### Actual Call Graph:
```
getClaims (service_impl)
  ├─ getMediumClaimBO (facade)  [dependencies: []]
  └─ populateGetClaimsOutPut (helper)
```

## Next Steps

1. Run `python test_with_debug.py` to see debug output
2. Check if pattern matching is happening
3. Check if DAO resolution is working
4. Add more detailed logging if needed
5. Fix the identified issue

## Contact Points

The key functions to investigate:
- `_trace_method_calls()` - Line ~125
- `_extract_method_calls()` - Line ~157
- `_resolve_method_call()` - Line ~210
- `_find_dao_method()` - Line ~281

All in `core/call_graph_builder.py`
