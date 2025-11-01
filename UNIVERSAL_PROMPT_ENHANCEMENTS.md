# Universal Prompt Enhancements for All APIs

## Summary

Added **generic, API-agnostic instructions** to `migrationPrompt.ts` that will improve migration accuracy for **ALL APIs**, not just `copyVisit`.

---

## ✅ What Was Added

### New Section: "SOURCE CODE ANALYSIS (MANDATORY FOR ALL APIs)"

This section teaches the LLM to **analyze source code systematically** before generating migrations, using **5 universal steps** that apply to any API.

---

## 📋 The 5-Step Analysis Process

### **STEP 1: Analyze ALL Variables in Source Code**

**Purpose**: Ensure no variables are skipped or merged

**Instructions**:
- Read the `source_code` field carefully for each node
- Identify ALL variables declared in the source code
- Example: If source has `SourceFoo sourceFoo = ...` and `DestFoo destFoo = ...`, create BOTH variables
- DO NOT merge, skip, or simplify variables

**Applies To**: All APIs (fetch, copy, transform, aggregate, etc.)

---

### **STEP 2: Detect Multiple Calls to Same Method**

**Purpose**: Catch when the same method is called multiple times with different parameters

**Instructions**:
- If the same method appears multiple times in source code, create separate operations for each call
- Example: If source has `getData(sourceId)` and `getData(destId)`, create TWO separate fetch operations
- Use different variable names: `source_data` and `dest_data`
- Check method dependencies - if a method appears 2+ times, it's called multiple times

**Applies To**:
- ✅ Copy/clone APIs (fetch source + fetch destination)
- ✅ Comparison APIs (fetch item1 + fetch item2)
- ✅ Merge APIs (fetch multiple datasets)
- ✅ Any API that processes multiple similar entities

---

### **STEP 3: Identify Data Flow Patterns**

**Purpose**: Understand the API's purpose and generate appropriate code

**4 Universal Patterns**:

1. **Fetch-Only Pattern**
   - Method fetches data and returns it
   - Example: `getPatientById`, `getClaimDetails`
   - Migration: Single fetch operation

2. **Copy/Clone Pattern**
   - Method fetches multiple datasets and combines/copies them
   - Look for: Multiple variables with similar names (`sourceFoo`, `destFoo`)
   - Look for: Setter calls like `destFoo.setField(sourceFoo.getField())`
   - Look for: Multiple calls to same fetch method with different parameters
   - Migration: Fetch source → Fetch destination → Copy fields → Save

3. **Transform Pattern**
   - Method fetches data, transforms it, and returns transformed version
   - Example: `convertClaimToDTO`, `calculateTotals`
   - Migration: Fetch → Transform → Return

4. **Aggregate Pattern**
   - Method fetches multiple datasets and aggregates them
   - Example: `getPatientSummary` (combines patient + visits + claims)
   - Migration: Fetch all datasets → Combine → Return

**Applies To**: All APIs

---

### **STEP 4: Preserve ALL Business Logic**

**Purpose**: Ensure 100% completeness - no logic is skipped

**Checklist**:
- ✅ Every if/else branch in source code MUST be in your code
- ✅ Every loop in source code MUST be in your code
- ✅ Every method call in source code MUST be in your code
- ✅ Every variable assignment in source code MUST be in your code
- ✅ If source code has 10 operations, your code must have 10 operations

**Applies To**: All APIs

---

### **STEP 5: Validate Before Generating**

**Purpose**: Self-check to catch missing logic before submitting

**Validation Counts**:
- Count variables in source code vs your code (must match)
- Count method calls in source code vs your code (must match)
- Count if/else branches in source code vs your code (must match)
- If counts don't match, you're missing logic - go back and add it

**Applies To**: All APIs

---

## 🎯 Common Patterns (Universal Examples)

### **Pattern A: Fetch Source + Fetch Destination + Copy**

**When This Applies**:
- APIs with "copy", "clone", "duplicate" in name
- APIs that transfer data from one entity to another
- APIs that merge data from multiple sources

**Java Source**:
```java
SourceEntity source = getEntity(sourceId);  // First call
DestEntity dest = getEntity(destId);        // Second call - SAME METHOD!
dest.setField(source.getField());           // Copy operation
save(dest);                                 // Save updated destination
```

**Python Migration**:
```python
# Fetch source
source_entity = fetch_entity(source_id)

# Fetch destination
dest_entity = fetch_entity(dest_id)

# Copy fields from source to destination
dest_entity['field'] = source_entity['field']

# Save updated destination
save_entity(dest_entity)
```

**Examples**:
- `copyVisit` - Copy visit data from source to destination
- `clonePatient` - Clone patient from template
- `duplicateClaim` - Duplicate claim with modifications
- `mergeAccounts` - Merge data from multiple accounts

---

### **Pattern B: Conditional Data Fetching**

**When This Applies**:
- APIs that fetch optional data based on flags
- APIs with conditional business logic
- APIs that build responses incrementally

**Java Source**:
```java
if (params.isIncludeDiagnosis()) {
    diagnosis = getDiagnosis(visitId);
}
```

**Python Migration**:
```python
diagnosis = None
if params.get('isIncludeDiagnosis'):
    diagnosis = get_diagnosis(visit_id)
```

**Examples**:
- `getPatientDetails` with optional flags (includeDiagnosis, includeVisits, etc.)
- `getClaimSummary` with conditional sections
- Any API with boolean parameters controlling data inclusion

---

### **Pattern C: Loop with Accumulation**

**When This Applies**:
- APIs that process lists/arrays
- APIs that transform collections
- APIs that aggregate data from multiple records

**Java Source**:
```java
List<Item> items = new ArrayList<>();
for (Source s : sources) {
    Item item = transform(s);
    items.add(item);
}
```

**Python Migration**:
```python
items = []
for source in sources:
    item = transform(source)
    items.append(item)
```

**Examples**:
- `getPatientVisits` - Loop through visits and transform each
- `calculateClaimTotals` - Loop through line items and sum
- `batchProcessClaims` - Process multiple claims in loop

---

## 🚩 RED FLAGS (Universal Warning Signs)

These indicate you're **simplifying or skipping logic** - applies to ALL APIs:

| Red Flag | What It Means | Fix |
|----------|---------------|-----|
| ❌ Source has 2 variables, your code has 1 | You merged variables | Create both variables |
| ❌ Source calls method twice, you call it once | You missed a call | Call the method twice with different params |
| ❌ Source has setter calls (setField), you don't | You skipped copy operations | Add all setter operations |
| ❌ Source has 5 if/else branches, you have 2 | You simplified conditionals | Add all branches |
| ❌ Source has loops, you don't | You skipped iteration | Add the loops |
| ❌ Your code is significantly shorter than source | You're simplifying | Add missing logic |

---

## 📊 Impact on Different API Types

### 1. **Copy/Clone APIs** (like copyVisit)
- ✅ Will now detect multiple calls to same method
- ✅ Will recognize copy pattern (source + dest + copy)
- ✅ Will preserve all setter operations
- ✅ Will not skip source data fetching

### 2. **Fetch APIs** (like getPatientById)
- ✅ Will preserve all conditional fetching
- ✅ Will not skip optional data
- ✅ Will maintain all if/else branches

### 3. **Transform APIs** (like convertToDTO)
- ✅ Will preserve all transformation logic
- ✅ Will not skip field mappings
- ✅ Will maintain all loops

### 4. **Aggregate APIs** (like getPatientSummary)
- ✅ Will fetch all required datasets
- ✅ Will preserve aggregation logic
- ✅ Will not skip any data sources

### 5. **Batch APIs** (like processClaims)
- ✅ Will preserve all loops
- ✅ Will maintain iteration logic
- ✅ Will not skip error handling

---

## 🎯 Key Improvements Over Previous Prompt

### Before:
```
32. **IMPLEMENT COMPLETE BUSINESS LOGIC:**
    - All business logic must be implemented while creating the nodes.
    - This includes all querying, validation, transformation, and error handling.
    - Do NOT skip or simplify any logic - this is a complete migration.
```

**Problem**: Too generic, no actionable steps

### After:
```
### CRITICAL: SOURCE CODE ANALYSIS (MANDATORY FOR ALL APIs)

**STEP 1: Analyze ALL Variables in Source Code**
- Read the source_code field carefully for each node
- Identify ALL variables declared in the source code
- Example: If source has "SourceFoo sourceFoo = ..." and "DestFoo destFoo = ...", you MUST create both variables
- DO NOT merge, skip, or simplify variables - preserve ALL of them

**STEP 2: Detect Multiple Calls to Same Method**
...

**STEP 3: Identify Data Flow Patterns**
...

**STEP 4: Preserve ALL Business Logic**
...

**STEP 5: Validate Before Generating**
...
```

**Improvement**: 
- ✅ Specific, actionable steps
- ✅ Concrete examples for each step
- ✅ Universal patterns that apply to all APIs
- ✅ Self-validation checklist
- ✅ Red flags to catch errors

---

## 📝 Testing Plan

### Test with Different API Types:

1. **Copy APIs**:
   - `copyVisit` - Should now fetch source + destination + copy
   - `clonePatient` - Should duplicate with modifications
   - `duplicateClaim` - Should copy claim data

2. **Fetch APIs**:
   - `getPatientById` - Should preserve all conditional fetching
   - `getClaimDetails` - Should include all optional data

3. **Transform APIs**:
   - `convertClaimToDTO` - Should preserve all field mappings
   - `calculateTotals` - Should maintain all calculations

4. **Aggregate APIs**:
   - `getPatientSummary` - Should fetch all data sources
   - `getDashboardData` - Should combine multiple datasets

5. **Batch APIs**:
   - `processClaims` - Should preserve loops and error handling
   - `batchUpdateVisits` - Should maintain iteration logic

---

## ✅ Expected Results

### For copyVisit (and similar Copy APIs):
- ✅ Fetch source data (was missing before)
- ✅ Fetch destination data (was present)
- ✅ Copy fields from source to destination (was missing before)
- ✅ Save updated destination (was present)
- ✅ All conditional copy operations (was missing before)

### For All Other APIs:
- ✅ All variables preserved
- ✅ All method calls preserved
- ✅ All if/else branches preserved
- ✅ All loops preserved
- ✅ No simplification or skipping

---

## 🔧 Files Modified

- ✅ `migrationPrompt.ts` - Lines 271-361 (new section added)

---

## 📚 Documentation Created

- ✅ `UNIVERSAL_PROMPT_ENHANCEMENTS.md` - This file
- ✅ `ROOT_CAUSE_ANALYSIS.md` - Detailed analysis of copyVisit issues
- ✅ `COPYVISIT_MIGRATION_ACCURACY_ANALYSIS.md` - Specific copyVisit findings

---

## 🎯 Conclusion

The new prompt enhancements are **100% generic and universal**:
- ✅ No API-specific instructions
- ✅ No hardcoded API names
- ✅ Works for copy, fetch, transform, aggregate, and batch APIs
- ✅ Teaches systematic source code analysis
- ✅ Provides universal patterns and examples
- ✅ Includes self-validation checklist

**Result**: All APIs will be migrated more accurately, not just `copyVisit`.
