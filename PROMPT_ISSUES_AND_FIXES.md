# Prompt Issues and Fixes

## Problem Identified

The LLM generated this **INCORRECT** code:

```python
query = '''
    SELECT * FROM medium_claim mc      # ❌ WRONG - Guessed table name
    WHERE mc.C_ID = :clinic_id         # ❌ WRONG - Used Java field name
    ORDER BY mc.DOS DESC
    LIMIT :count OFFSET :offset
'''
```

## Issues

### 1. ❌ **Wrong Table Name**
- **Generated**: `medium_claim` (guessed by snake_casing Java entity name)
- **Should be**: `CLAIM` (from `metadata.entities.MediumClaim.table_name`)

### 2. ❌ **Wrong Column Name**
- **Generated**: `C_ID` (used Java field name directly)
- **Should be**: `CLINIC_ID` (from `metadata.entities.MediumClaim.fields.C_ID.column`)

### 3. ❌ **Ignoring Metadata**
The LLM completely ignored the metadata and guessed names instead!

---

## Root Cause

The original prompt had instructions but they were **not emphatic enough**. The LLM needs:
1. **Stronger warnings** at the top
2. **Step-by-step mandatory instructions**
3. **WRONG vs RIGHT examples**
4. **Verification checklist**

---

## Fixes Applied

### Fix 1: Added Critical Warnings at Top

```typescript
const base = [
    `You are an expert Java-to-Python migration specialist...`,
    ``,
    `⚠️ CRITICAL: The migration JSON contains metadata.entities and metadata.enums that you MUST use for ALL table/column/enum lookups.`,
    `⚠️ DO NOT guess or invent table/column names. ALWAYS look them up in metadata.entities.`,
    `⚠️ DO NOT hardcode enum values. ALWAYS look them up in metadata.enums.`,
    ``,
    // ... rest of prompt
];
```

### Fix 2: Added Mandatory Step-by-Step Instructions

```typescript
`4. **Hibernate Query Translation (MANDATORY STEPS)**:`,
`   `,
`   Step 1: Identify the Java entity name in HQL (e.g., "MediumClaim")`,
`   Step 2: Look up metadata.entities[EntityName].table_name for the actual table name`,
`   Step 3: For each field reference (e.g., mc.C_ID):`,
`           - Look up metadata.entities[EntityName].fields[FieldName].column`,
`           - Use the actual column name from metadata`,
`   Step 4: Build SQL query with actual table and column names`,
`   Step 5: Use parameterized queries with text()`,
`   `,
`   ⚠️ NEVER use Java entity names directly in SQL (e.g., "medium_claim" is WRONG)`,
`   ⚠️ NEVER use Java field names directly in SQL (e.g., "C_ID" might be WRONG)`,
`   ⚠️ ALWAYS look up the actual database names in metadata.entities`,
```

### Fix 3: Added WRONG vs RIGHT Example

```typescript
`**Example 1: Simple Query (WRONG vs RIGHT)**`,
``,
`Java HQL: "from MediumClaim mc where mc.C_ID = " + clinicId`,
``,
`Given metadata:`,
`{`,
`  "entities": {`,
`    "MediumClaim": {`,
`      "table_name": "CLAIM",`,
`      "fields": {`,
`        "C_ID": {"column": "CLINIC_ID"}`,
`      }`,
`    }`,
`  }`,
`}`,
``,
`❌ WRONG (guessing names):`,
`\`\`\`python`,
`query = "SELECT * FROM medium_claim mc WHERE mc.C_ID = :clinic_id"  # WRONG!`,
`\`\`\``,
``,
`✅ RIGHT (using metadata):`,
`\`\`\`python`,
`# Lookup: metadata.entities.MediumClaim.table_name = "CLAIM"`,
`# Lookup: metadata.entities.MediumClaim.fields.C_ID.column = "CLINIC_ID"`,
`query = "SELECT * FROM CLAIM mc WHERE mc.CLINIC_ID = :clinic_id"  # CORRECT!`,
`\`\`\``,
```

### Fix 4: Added Verification Checklist

```typescript
`### MANDATORY VERIFICATION CHECKLIST:`,
``,
`Before generating each SQL query, verify:`,
``,
`□ Did I look up the table name in metadata.entities[EntityName].table_name?`,
`□ Did I look up EVERY column name in metadata.entities[EntityName].fields[FieldName].column?`,
`□ Am I using the ACTUAL database names from metadata, not Java names?`,
`□ Did I avoid guessing or snake_casing Java entity names?`,
`□ Did I look up enum values in metadata.enums?`,
`□ Did I check metadata.helper_methods for any helper calls?`,
`□ Did I follow node.logic_annotations recommendations?`,
```

### Fix 5: Strengthened Final Reminders

```typescript
`### FINAL REMINDERS:`,
`- ⚠️ CRITICAL: ALWAYS use metadata.entities for table and column name lookups`,
`- ⚠️ CRITICAL: ALWAYS use metadata.enums for enum value lookups`,
`- ⚠️ CRITICAL: NEVER guess table/column names by converting Java names to snake_case`,
`- ALWAYS check metadata.helper_methods for helper implementations`,
`- ALWAYS follow node.logic_annotations recommendations`,
`- PRESERVE all business logic from Java source`,
`- Use parameterized queries for SQL injection prevention`,
`- Return only valid JSON, no markdown or explanations`,
```

---

## Expected Output After Fixes

With the updated prompt, the LLM should generate:

```python
from sqlalchemy import text
try:
    if not input_data.get('ok'):
        return input_data
    
    offset = input_data['data']['offset']
    count = input_data['data']['count']
    clinic_id = input_data['data']['clinic_id']
    
    # Lookup: metadata.entities.MediumClaim.table_name = "CLAIM"
    # Lookup: metadata.entities.MediumClaim.fields.C_ID.column = "CLINIC_ID"
    # Lookup: metadata.entities.MediumClaim.fields.DOS.column = "DOS"
    
    query = '''
        SELECT * FROM CLAIM mc              # ✅ CORRECT - From metadata
        WHERE mc.CLINIC_ID = :clinic_id     # ✅ CORRECT - From metadata
        ORDER BY mc.DOS DESC                # ✅ CORRECT - From metadata
        LIMIT :count OFFSET :offset
    '''
    
    params = {"clinic_id": clinic_id, "count": count, "offset": offset}
    rows = db.execute(text(query), params).mappings().all()
    claims = [dict(row) for row in rows]
    
    return {"ok": True, "data": {"claims": claims, "count": len(claims)}}
    
except Exception as e:
    return {
        "ok": False, 
        "status": 500, 
        "message": "Database error", 
        "error": {"type": type(e).__name__, "details": str(e)}
    }
```

---

## Testing the Updated Prompt

1. **Verify metadata is in JSON**: Ensure your migration JSON includes:
   ```json
   {
     "metadata": {
       "entities": {
         "MediumClaim": {
           "table_name": "CLAIM",
           "fields": {
             "C_ID": {"column": "CLINIC_ID"},
             "DOS": {"column": "DOS"}
           }
         }
       }
     }
   }
   ```

2. **Test with the same API**: Re-run the LLM with the updated prompt

3. **Check the output**: Verify it uses:
   - `CLAIM` (not `medium_claim`)
   - `CLINIC_ID` (not `C_ID`)
   - Comments showing metadata lookups

---

## Additional Recommendations

### 1. Use Few-Shot Examples in User Message

In addition to the system prompt, add examples in the user message:

```typescript
{
    role: 'user',
    content: `### MIGRATION JSON:
${JSON.stringify(migrationJson, null, 2)}

### IMPORTANT REMINDERS:
- Use metadata.entities.MediumClaim.table_name for table name
- Use metadata.entities.MediumClaim.fields.C_ID.column for column names
- DO NOT guess or snake_case Java names`
}
```

### 2. Use GPT-4o or GPT-4-turbo

The updated prompt uses `gpt-4o` which is better at following complex instructions.

### 3. Add Metadata Validation

Before sending to LLM, verify metadata is present:

```typescript
if (!migrationJson.metadata?.entities) {
    throw new Error('Migration JSON missing metadata.entities!');
}
```

### 4. Post-Process LLM Output

Add validation to check if LLM used correct names:

```typescript
function validateGeneratedCode(code: string, metadata: any): boolean {
    // Check if code contains Java entity names (should not)
    const javaEntities = Object.keys(metadata.entities);
    for (const entity of javaEntities) {
        const snakeCased = entity.replace(/([A-Z])/g, '_$1').toLowerCase();
        if (code.includes(snakeCased)) {
            console.warn(`⚠️ Found snake_cased entity name: ${snakeCased}`);
            return false;
        }
    }
    
    // Check if code contains actual table names (should)
    const tableNames = Object.values(metadata.entities).map(e => e.table_name);
    // ... validation logic
    
    return true;
}
```

---

## Summary

The prompt has been **significantly strengthened** with:

✅ **Critical warnings** at the top  
✅ **Mandatory step-by-step** instructions  
✅ **WRONG vs RIGHT** examples  
✅ **Verification checklist**  
✅ **Stronger final reminders**  

This should force the LLM to use metadata correctly and stop guessing names!

**Next Step**: Test with the updated prompt and verify the output uses correct table/column names from metadata.
