# Migration Prompt Fixes Applied ✅

## Summary

Fixed three critical issues in `migrationPrompt.ts` that were causing the LLM to generate incomplete code without database operations.

---

## ✅ Fix 1: Corrected Metadata Pruning (Lines 68-97)

### Problem
The pruning function was removing critical database schema information:
- ❌ Table names were removed
- ❌ Column names were removed  
- ❌ Data types were removed
- ❌ Only field names as string arrays remained

### Solution
Modified `pruneCallGraphForLLM()` to preserve essential database schema:

```typescript
// OLD (WRONG):
optimizedEntities[entityName] = Object.keys(entity.fields);  // Just field names

// NEW (CORRECT):
optimizedEntities[entityName] = {
    table_name: entity.table_name || entityName.toLowerCase(),
    fields: {
        fieldName: {
            column: field.column || fieldName.toLowerCase(),
            type: field.type || 'VARCHAR',
            nullable: field.nullable !== false
        }
    }
};
```

### What LLM Now Receives
```json
{
  "metadata": {
    "entities": {
      "CopyVisit": {
        "table_name": "copy_visit",
        "fields": {
          "iVisitId": {
            "column": "i_visit_id",
            "type": "INTEGER",
            "nullable": false
          },
          "iPatientId": {
            "column": "i_patient_id",
            "type": "INTEGER",
            "nullable": false
          }
        }
      }
    }
  }
}
```

**Impact**: LLM now knows exact table and column names for SQL generation.

---

## ✅ Fix 2: Added HQL-to-SQL Conversion Instructions (Lines 233-270)

### Problem
- ❌ No instructions on how to convert HQL to SQL
- ❌ No Hibernate-to-Python method mappings
- ❌ No examples of conversion
- ❌ Weak enforcement (just "implement database queries")

### Solution
Added comprehensive HQL-to-SQL conversion guide with:

#### Translation Rules
```
1. HQL: "from EntityName e where e.field = ?" 
   → SQL: "SELECT * FROM table_name WHERE column_name = :param"

2. Entity names (CopyVisit) → Table names from metadata.entities[EntityName].table_name

3. Field names (e.iVisitId) → Column names from metadata.entities[EntityName].fields[fieldName].column

4. Positional params (?) → Named params (:param_name)

5. Use metadata.entities to lookup exact table and column names
```

#### Hibernate Method Mappings
```
- getHibernateTemplate().find(hql, params) 
  → db.execute(text(sql), params_dict).mappings().all()

- getHibernateTemplate().saveOrUpdate(entity) 
  → db.execute(text("INSERT ... ON DUPLICATE KEY UPDATE ..."))

- session.save(entity) 
  → db.execute(text("INSERT INTO ..."))

- session.update(entity) 
  → db.execute(text("UPDATE ... SET ..."))
```

#### Complete Example
```python
# Java Source:
String sQry = "from CopyVisit v where v.iVisitId = ? and v.iClinicId = ?";
List<CopyVisit> resultList = getHibernateTemplate().find(sQry, new Object[] { iVisitId, iClinicId });

# Python Conversion (using metadata):
# metadata.entities["CopyVisit"].table_name = "copy_visit"
# metadata.entities["CopyVisit"].fields["iVisitId"].column = "i_visit_id"
sql = "SELECT * FROM copy_visit WHERE i_visit_id = :visit_id AND i_clinic_id = :clinic_id"
result = db.execute(text(sql), {'visit_id': iVisitId, 'clinic_id': iClinicId}).mappings().all()
copy_visits = [dict(row) for row in result]
```

#### Critical Enforcement
```
- DO NOT use mock data, synthetic IDs, or hardcoded values
- DO NOT add placeholder comments like "# In a full migration..." or "# TODO: implement DB query"
- DO NOT skip database operations - every HQL query MUST become a SQL query
- If you see getHibernateTemplate() in source code, you MUST generate db.execute() in Python
- If you see HQL strings in source code, you MUST generate SQL strings in Python
```

**Impact**: LLM now has clear, explicit instructions on how to convert Hibernate code to Python SQL.

---

## ✅ Fix 3: Replaced Incomplete Example with Complete DB Query Example (Lines 363-451)

### Problem
The old example had placeholder comments that taught bad habits:
```python
# OLD EXAMPLE (WRONG):
code: "def validate_payload(d):\\n    # ... rest of validation\\n    return result"
```

This taught the LLM that placeholder comments are acceptable.

### Solution
Replaced with a **complete database query example** showing:
- ✅ Full HQL-to-SQL conversion
- ✅ Proper metadata usage
- ✅ Complete error handling
- ✅ Actual database operations
- ✅ No placeholder comments

```python
# NEW EXAMPLE (CORRECT):
code: """
# Original: VisitDaoImpl.getVisitByVisitId(int iVisitId, int iClinicId)
# Java Source: String sQry = "from Visit v where v.iVisitId = ? and v.iClinicId = ?"
# Java Source: List<Visit> resultList = getHibernateTemplate().find(sQry, new Object[] { iVisitId, iClinicId })

from sqlalchemy import text

try:
    visit_id = input_data.get('visitId')
    clinic_id = input_data.get('clinicId')
    
    if not visit_id or not clinic_id:
        result = { 'ok': False, 'status': 400, 'message': 'Missing visitId or clinicId', 'error': { 'type': 'ValidationError' } }
        return result
    
    # Convert HQL to SQL using metadata
    # metadata.entities["Visit"].table_name = "visit"
    # metadata.entities["Visit"].fields["iVisitId"].column = "i_visit_id"
    sql = "SELECT i_visit_id, i_patient_id, i_clinic_id, dos, visit_status FROM visit WHERE i_visit_id = :visit_id AND i_clinic_id = :clinic_id"
    
    result_proxy = db.execute(text(sql), {'visit_id': visit_id, 'clinic_id': clinic_id}).mappings()
    visit_row = result_proxy.first()
    
    if not visit_row:
        result = { 'ok': False, 'status': 404, 'message': 'Visit not found', 'error': { 'type': 'NotFound' } }
        return result
    
    visit_data = dict(visit_row)
    result = { 'data': { 'visit': visit_data } }
    return result
    
except Exception as e:
    result = { 'ok': False, 'status': 500, 'message': 'Database error', 'error': { 'type': type(e).__name__, 'details': str(e) } }
    return result
"""
```

**Impact**: LLM now learns from a complete, working example with actual database operations.

---

## ✅ Preserved Rules 11, 12, 13

The original database connection rules were preserved exactly as requested:

```typescript
`10- The following variables already exist in scope:`,
`11 - db: an injected database session/connection`,
`12- For ANY SQL/database task:`,
`13  - Wrap SQL strings with text("...") and use named placeholders like :param.`,
` 14 - Call db.execute(text(<sql>), <params>) with a params dict.`,
```

These rules remain unchanged and are now reinforced by the new HQL-to-SQL conversion instructions.

---

## Expected Results

### Before Fixes
```python
# LLM Generated (WRONG):
copyClaimInfoBO = {
    'copyVisit': { 'iVisitId': iVisitId, 'iPatientId': 0, 'iClinicId': iClinicId },
    # ... hardcoded mock data
}
```

**Issues:**
- ❌ No database queries
- ❌ Mock/synthetic data
- ❌ 100% data loss

### After Fixes
```python
# LLM Should Generate (CORRECT):
# Original: ClaimInfoBODaoImpl.getCopyClaimInfoBO()

# Convert HQL: "from CopyVisit v where v.iVisitId = ? and v.iClinicId = ?"
sql = "SELECT i_visit_id, i_patient_id, i_clinic_id FROM copy_visit WHERE i_visit_id = :visit_id AND i_clinic_id = :clinic_id"
copy_visit_result = db.execute(text(sql), {'visit_id': iVisitId, 'clinic_id': iClinicId}).mappings().first()

# Convert HQL: "from CopyClaim c where c.iClaimId = ? and c.iClinicId = ?"
sql = "SELECT i_claim_id, i_clinic_id FROM copy_claim WHERE i_claim_id = :claim_id AND i_clinic_id = :clinic_id"
copy_claim_result = db.execute(text(sql), {'claim_id': iClaimId, 'clinic_id': iClinicId}).mappings().first()

copyClaimInfoBO = {
    'copyVisit': dict(copy_visit_result) if copy_visit_result else None,
    'copyClaim': dict(copy_claim_result) if copy_claim_result else None,
    # ... actual database queries for other fields
}
```

**Expected:**
- ✅ Real database queries
- ✅ Actual data from database
- ✅ 0% data loss
- ✅ Complete implementation

---

## Testing

To verify the fixes work:

1. **Clear any cached call graphs**
2. **Regenerate the copyVisit API migration**
3. **Check generated code for:**
   - ✅ `db.execute(text(...))` calls in DAO nodes
   - ✅ SQL queries (not HQL)
   - ✅ Table names from metadata (e.g., `copy_visit`)
   - ✅ Column names from metadata (e.g., `i_visit_id`)
   - ✅ No placeholder comments
   - ✅ No mock/synthetic data

---

## Files Modified

- ✅ `migrationPrompt.ts` - Lines 68-97 (metadata pruning)
- ✅ `migrationPrompt.ts` - Lines 233-270 (HQL-to-SQL instructions)
- ✅ `migrationPrompt.ts` - Lines 363-451 (complete example)

---

## Conclusion

All three critical issues have been fixed:

1. ✅ **Metadata now includes table names, column names, and types**
2. ✅ **LLM has explicit HQL-to-SQL conversion instructions**
3. ✅ **Example shows complete database query implementation**

The LLM should now generate complete, working code with actual database operations instead of mock data.
