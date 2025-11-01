# Prompt Engineering Guide - Faithful API Migration

## Overview

The enhanced prompt engineering system ensures **100% faithful migration** from Java SOAP APIs to Python REST APIs while preserving:
- ✅ Exact method naming
- ✅ Identical response structure
- ✅ Original logical flow
- ✅ Complete traceability
- ✅ Sequential execution (no parallel calls)

## 🎯 8 Critical Migration Principles

### **PRINCIPLE 1: PRESERVE ORIGINAL STRUCTURE**

**What**: The migrated API must mirror the original API's structure exactly.

**Why**: This is a migration, not a rewrite. Developers need to trace between old and new code.

**How**:
- Method names stay identical (e.g., `getCopyClaimInfoBO`, not `get_copy_claim_info`)
- Function organization remains the same
- Logical flow is preserved

**Example**:
```java
// Original Java
public CopyClaimInfoBO getCopyClaimInfoBO(params) {
    // ... logic ...
}
```

```python
# Migrated Python - Node name: "getCopyClaimInfoBO"
# Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO()
def get_copy_claim_info_bo(params):
    # ... same logic ...
```

---

### **PRINCIPLE 2: IDENTICAL RESPONSE STRUCTURE**

**What**: API responses must be 100% identical between old and new APIs.

**Why**: Frontend applications depend on exact field names, nesting, and data types.

**How**:
- Preserve exact field names (including Hungarian notation: `iVisitId`, `sFirstName`)
- Maintain nesting structure
- Keep array structures identical
- Match null/empty handling
- Preserve data types

**Example**:
```json
// Original Java Response
{
  "copyClaimInfoBO": {
    "iVisitId": 12345,
    "sPatientName": "John Doe",
    "visitDiagnosis": {
      "iICD1": 101,
      "sICD1Code": "A01.1"
    },
    "procedures": [
      { "iProcedureId": 1, "sCPTCode": "99213" }
    ]
  }
}

// Migrated Python Response - MUST BE IDENTICAL
{
  "copyClaimInfoBO": {
    "iVisitId": 12345,
    "sPatientName": "John Doe",
    "visitDiagnosis": {
      "iICD1": 101,
      "sICD1Code": "A01.1"
    },
    "procedures": [
      { "iProcedureId": 1, "sCPTCode": "99213" }
    ]
  }
}
```

**Test**: `JSON.stringify(old_response) === JSON.stringify(new_response)` must be TRUE.

---

### **PRINCIPLE 3: PRESERVE METHOD NAMING**

**What**: Use EXACT method names from the original API.

**Why**: Enables easy debugging and comparison between old and new code.

**How**:
- Node `nodeName`: Use original Java method name in camelCase
- Node `objectName`: Convert to snake_case
- Do NOT rename to follow modern conventions

**Example**:
```javascript
// ✅ CORRECT
{
  nodeName: "getCopyClaimInfoBO",
  objectName: "get_copy_claim_info_bo"
}

// ❌ WRONG - Don't invent new names
{
  nodeName: "fetchClaimInfo",
  objectName: "fetch_claim_info"
}
```

---

### **PRINCIPLE 4: PRESERVE LOGICAL SPLITTING**

**What**: If the original API splits logic into separate methods, create separate nodes.

**Why**: Maintains the same debugging granularity as the original.

**How**:
- One node per original method
- Preserve method boundaries
- Don't merge or split logic differently

**Example**:
```java
// Original Java - Two separate methods
public CopyClaimInfoBO getCopyClaimInfoBO(params) { ... }
public void storeOrUpdateCopyClaimInfoBO(data) { ... }
```

```javascript
// Migrated - Two separate nodes
{
  __NODE2__: {
    nodeName: "getCopyClaimInfoBO",
    // ... code ...
  },
  __NODE3__: {
    nodeName: "storeOrUpdateCopyClaimInfoBO",
    // ... code ...
  }
}
```

---

### **PRINCIPLE 5: SEQUENTIAL FLOW (NO PARALLEL EXECUTION)**

**What**: Convert parallel method calls to sequential execution.

**Why**: Simplifies debugging and ensures predictable execution order.

**How**:
- If original calls methods A and B in parallel, make it A → B sequentially
- Use linear node connections
- Clear execution order

**Example**:
```java
// Original Java - Parallel calls
if (params.isblCopyDiagnosis()) {
    diagnosisData = getDiagnosis(visitId);  // Parallel
}
if (params.isblCopyProcedures()) {
    procedureData = getProcedures(visitId); // Parallel
}
```

```javascript
// Migrated - Sequential
__NODE2__ → getDiagnosis → __NODE3__ → getProcedures → __NODE4__
```

---

### **PRINCIPLE 6: TRACEABILITY**

**What**: Every function in the original API must have a corresponding node with clear traceability.

**Why**: Developers need to map between old and new implementations.

**How**:
- Add comments referencing original Java method
- Use descriptive node names matching original
- Maintain same method granularity

**Example**:
```python
# Node code
# Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO()
def get_copy_claim_info_bo(input_data):
    # ... implementation ...
```

---

### **PRINCIPLE 7: COMPLETE BUSINESS LOGIC**

**What**: Implement ALL business logic from the original API.

**Why**: This is a complete migration, not a partial implementation.

**How**:
- Include all conditional branches (if/else)
- Implement all data transformations
- Execute all database queries
- Handle all validations
- Preserve all error handling

**Example**:
```java
// Original Java
if (params.isblCopyDiagnosis()) {
    diagnosis = getDiagnosis(visitId);
    if (diagnosis != null) {
        copyClaimInfoBO.setVisitDiagnosis(diagnosis);
    }
}
```

```python
# Migrated - Preserve ALL logic
if input_data.get('isblCopyDiagnosis'):
    diagnosis = get_diagnosis(visit_id)
    if diagnosis is not None:
        copy_claim_info_bo['visitDiagnosis'] = diagnosis
```

---

### **PRINCIPLE 8: RESPONSE COMPATIBILITY**

**What**: Responses from old and new APIs must be identical for identical inputs.

**Why**: Frontend applications will break if responses change.

**How**:
- Test with same inputs
- Compare responses byte-by-byte
- Ensure JSON equality

**Test**:
```javascript
// Must be true
const oldResponse = callOldAPI(input);
const newResponse = callNewAPI(input);
assert(JSON.stringify(oldResponse) === JSON.stringify(newResponse));
```

---

## 📋 Prompt Structure

### 1. Critical Principles Section
- 8 principles listed above
- Emphasized with bold headers
- Clear explanations

### 2. Response Structure Requirements
- Preserve exact field names
- Preserve nesting structure
- Preserve array structures
- Preserve null handling
- Preserve data types
- Use call graph metadata
- Response compatibility test

### 3. Node Organization Requirements
- Create nodes for each original method
- Preserve execution order
- Add traceability comments
- Preserve conditional logic
- Implement complete business logic
- Database query optimization

### 4. Technical Rules
- JSON format requirements
- Node naming conventions
- Connection patterns
- Database access patterns
- Variable scoping rules

---

## 🎯 Key Enhancements Made

### Before (Generic Migration)
```typescript
`You are an API flow migration assistant.`
`You may split, merge, or reorganize logic as you see fit`
```

### After (Faithful Migration)
```typescript
`You are an API migration assistant specializing in FAITHFUL, STRUCTURE-PRESERVING migrations.`
`DO NOT split, merge, or reorganize logic - preserve the original method organization.`
```

### Before (Generic Naming)
```typescript
`nodeName: Use valid camelCase identifiers (e.g., "getClaimsApi", "validateInput")`
```

### After (Preserve Original Names)
```typescript
`nodeName: Use the EXACT method name from the original API in camelCase (e.g., "getCopyClaimInfoBO")`
`DO NOT invent new names - use the original Java method names for traceability.`
```

### Before (No Response Requirements)
```typescript
// No specific response structure requirements
```

### After (Strict Response Requirements)
```typescript
`PRESERVE EXACT FIELD NAMES: Use the EXACT field names from the original API response`
`PRESERVE NESTING STRUCTURE: Do NOT flatten or restructure nested objects`
`RESPONSE COMPATIBILITY TEST: responses must be JSON-equal`
```

---

## 📊 Validation Checklist

Before using the migrated API, verify:

### Structure Preservation
- [ ] All original method names are preserved in node names
- [ ] Node organization matches original method organization
- [ ] Execution order follows original call graph
- [ ] Logical splitting is identical to original

### Response Compatibility
- [ ] Field names match exactly (including Hungarian notation)
- [ ] Nesting structure is identical
- [ ] Array structures are preserved
- [ ] Null/empty handling matches original
- [ ] Data types are identical

### Traceability
- [ ] Each node has a comment referencing original Java method
- [ ] Node names match original method names
- [ ] Developers can easily map between old and new code

### Completeness
- [ ] All conditional branches are implemented
- [ ] All database queries are included
- [ ] All validations are present
- [ ] All error handling is preserved
- [ ] All data transformations are implemented

---

## 🚀 Usage Example

### Input: Call Graph JSON
```json
{
  "api_name": "copyVisit",
  "nodes": [
    {
      "name": "copyVisit",
      "class_name": "ClaimServiceImpl",
      "node_type": "service_impl"
    },
    {
      "name": "saveCopyClaimByCopyVisitParams",
      "class_name": "ClaimInfoBODaoImpl",
      "node_type": "dao"
    },
    {
      "name": "getCopyClaimInfoBO",
      "class_name": "ClaimInfoBODaoImpl",
      "node_type": "dao"
    },
    {
      "name": "storeOrUpdateCopyClaimInfoBO",
      "class_name": "ClaimInfoBODaoImpl",
      "node_type": "dao"
    }
  ],
  "edges": [...],
  "metadata": {
    "entities": {...},
    "enums": {...}
  }
}
```

### Output: Migrated API JSON
```json
{
  "name": "copy_visit",
  "active": true,
  "nodes": {
    "__NODE1__": {
      "id": "__NODE1__",
      "type": "api",
      "nodeName": "copyVisitApi",
      "objectName": "copy_visit",
      "data": {
        "parameters": {
          "apiName": "copyVisitApi",
          "httpMethod": "POST",
          "path": "/copy_visit",
          "apiDescription": "Copy visit data including diagnosis, procedures, providers, etc."
        }
      }
    },
    "__NODE2__": {
      "id": "__NODE2__",
      "type": "code",
      "nodeName": "saveCopyClaimByCopyVisitParams",
      "objectName": "save_copy_claim_by_copy_visit_params",
      "data": {
        "parameters": {
          "prompt": "Orchestrate the copy visit operation",
          "code": "# Original: ClaimInfoBODaoImpl.saveCopyClaimByCopyVisitParams()\\n..."
        }
      }
    },
    "__NODE3__": {
      "id": "__NODE3__",
      "type": "code",
      "nodeName": "getCopyClaimInfoBO",
      "objectName": "get_copy_claim_info_bo",
      "data": {
        "parameters": {
          "prompt": "Fetch copy claim info including diagnosis, procedures, etc.",
          "code": "# Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO()\\n..."
        }
      }
    },
    "__NODE4__": {
      "id": "__NODE4__",
      "type": "code",
      "nodeName": "storeOrUpdateCopyClaimInfoBO",
      "objectName": "store_or_update_copy_claim_info_bo",
      "data": {
        "parameters": {
          "prompt": "Store or update the copied claim info",
          "code": "# Original: ClaimInfoBODaoImpl.storeOrUpdateCopyClaimInfoBO()\\n..."
        }
      }
    },
    "__NODE5__": {
      "id": "__NODE5__",
      "type": "code",
      "nodeName": "formatResponse",
      "objectName": "format_response",
      "data": {
        "isLastNode": true,
        "parameters": {
          "prompt": "Format response to match original API structure",
          "code": "# Preserve exact field names and nesting structure\\n..."
        }
      }
    }
  },
  "connections": {
    "edge-__NODE1__-__NODE2__": {...},
    "edge-__NODE2__-__NODE3__": {...},
    "edge-__NODE3__-__NODE4__": {...},
    "edge-__NODE4__-__NODE5__": {...}
  }
}
```

---

## 🎁 Benefits

### For Developers
- ✅ Easy to debug by comparing with original code
- ✅ Clear traceability between old and new implementations
- ✅ Familiar method names and structure
- ✅ No surprises in behavior

### For Frontend Teams
- ✅ No changes needed to frontend code
- ✅ API responses remain identical
- ✅ No breaking changes
- ✅ Seamless migration

### For QA Teams
- ✅ Easy to verify correctness
- ✅ Can compare responses directly
- ✅ Clear test cases (old vs new)
- ✅ Predictable behavior

### For Business
- ✅ Zero downtime migration
- ✅ No frontend rework needed
- ✅ Reduced risk
- ✅ Faster migration timeline

---

## 🔧 Configuration

The prompt is configured in `migrationPrompt.ts`:

```typescript
function getApiMigrationScaffoldPrompt(): string {
    const base = [
        `You are an API migration assistant specializing in FAITHFUL, STRUCTURE-PRESERVING migrations.`,
        // ... 8 critical principles ...
        // ... Response structure requirements ...
        // ... Node organization requirements ...
        // ... Technical rules ...
    ].join('\n');
    return base;
}
```

---

## 📚 Related Documentation

- **COMPLETE_CALL_GRAPH_MODE.md** - How to generate complete call graphs
- **VALIDATION_GUIDE.md** - How to validate call graph accuracy
- **README_VALIDATION.md** - Quick validation reference

---

## 🎯 Success Criteria

A successful migration meets ALL these criteria:

1. ✅ **Structure Preserved**: Method names and organization match original
2. ✅ **Response Identical**: `old_response == new_response` for all inputs
3. ✅ **Traceable**: Developers can easily map between old and new code
4. ✅ **Complete**: All business logic implemented
5. ✅ **Sequential**: Clear execution order (no parallel calls)
6. ✅ **Compatible**: Frontend works without any changes
7. ✅ **Validated**: Call graph accuracy ≥ 95%
8. ✅ **Tested**: Responses verified to be identical

---

**Your prompt engineering is now configured for faithful, structure-preserving API migration!** 🎉
