# Call Graph Validation Guide

## Overview

This validation system cross-verifies generated call graphs against actual Java source code to ensure 100% accuracy. It checks:

✅ **Method Coverage** - All methods are traced  
✅ **Query Coverage** - All SQL/HQL queries are captured  
✅ **Return Types** - Return types match actual code  
✅ **Parameters** - Parameter definitions are accurate  
✅ **Conditional Branches** - All if/else/switch/try-catch are explored  
✅ **DAO Operations** - All database operations are included  

## Quick Start

### Validate a Single API

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows Git Bash
# or
venv\Scripts\activate  # Windows CMD

# Run validation
python test_api_validation.py ClaimService copyVisit
```

### Expected Output

```
================================================================================
Validating API: ClaimService.copyVisit
================================================================================

1. Generating call graph...
   ✓ Generated 156 nodes, 245 edges

2. Extracting actual method calls from Java source...
   ✓ Found 142 actual method calls in source code

3. Extracting SQL/HQL queries from Java source...
   ✓ Found 23 SQL/HQL queries in source code

4. Validating method coverage...
   ✓ All actual methods are in call graph
   Coverage: 100.0%

5. Validating query coverage...
   ✓ Found 23 queries in 18 nodes

6. Validating return types...
   ✓ All return types appear accurate

7. Validating parameter definitions...
   ✓ All parameters appear to be used correctly

8. Validating conditional branches...
   ✓ Found 87 conditional branches:
      - if statements: 45
      - else statements: 23
      - switch statements: 2
      - try-catch blocks: 12
      - loops: 5

9. Validating DAO operations...
   ✓ Found 34 DAO nodes:
      - GET operations: 18
      - SAVE/STORE operations: 10
      - UPDATE operations: 4
      - DELETE operations: 2

================================================================================
VALIDATION SUMMARY
================================================================================

📊 Overall Accuracy: 98.5%
   ✅ EXCELLENT - Call graph is highly accurate

📈 Detailed Scores:
   - Method Coverage: 100.0%
   - Total Nodes: 156
   - Total Edges: 245
   - SQL/HQL Queries: 23
   - DAO Operations: 34
   - Conditional Branches: 87

📄 Reports saved:
   - JSON: output/validation_reports/ClaimService_copyVisit_validation.json
   - Text: output/validation_reports/ClaimService_copyVisit_report.txt

================================================================================
✅ VALIDATION PASSED
   Accuracy: 98.5%
   The call graph accurately represents the API logic.
================================================================================
```

## What Gets Validated

### 1. Method Coverage (40% weight)

Compares methods in the call graph vs. actual method calls in Java source code.

**Pass Criteria**: ≥95% of actual methods are in the call graph

**Example**:
```
Actual methods in Java: 142
Methods in call graph: 142
Coverage: 100% ✅
```

### 2. Query Coverage (20% weight)

Identifies all SQL/HQL queries in the source code.

**Pass Criteria**: All queries are captured in node source code

**Example**:
```
SQL queries found: 15
HQL queries found: 8
Total: 23 queries in 18 nodes ✅
```

### 3. Return Type Accuracy (15% weight)

Validates that return types match return statements.

**Pass Criteria**: No mismatches between declared return type and actual returns

**Example**:
```
Node: getCopyClaimInfoBO
Return type: CopyClaimInfoBO
Return statement: return copyClaimInfoBO; ✅
```

### 4. Parameter Accuracy (10% weight)

Checks that all parameters are properly defined and used.

**Pass Criteria**: Parameters are used in method body

**Example**:
```
Parameter: int visitId
Used in code: visitDao.getVisit(visitId) ✅
```

### 5. Conditional Branch Coverage (10% weight)

Counts all conditional logic in the code.

**Pass Criteria**: Branches are present in traced methods

**Example**:
```
if(params.isblCopyDiagnosis()) { ... } ✅
else { ... } ✅
try { ... } catch { ... } ✅
```

### 6. DAO Operation Coverage (5% weight)

Validates database operations are captured.

**Pass Criteria**: DAO nodes exist with proper operations

**Example**:
```
GET: visitDao.getVisit() ✅
SAVE: claimDao.saveClaim() ✅
UPDATE: diagnosisDao.updateDiagnosis() ✅
```

## Accuracy Scoring

### Overall Score Calculation

```
Overall Accuracy = 
  (Method Coverage × 0.40) +
  (Query Coverage × 0.20) +
  (Return Type Accuracy × 0.15) +
  (Parameter Accuracy × 0.10) +
  (Branch Coverage × 0.10) +
  (DAO Coverage × 0.05)
```

### Rating Scale

| Score | Rating | Meaning |
|-------|--------|---------|
| 95-100% | ✅ EXCELLENT | Call graph is highly accurate |
| 80-94% | ✅ GOOD | Call graph is accurate with minor issues |
| 60-79% | ⚠️ FAIR | Call graph has some accuracy issues |
| <60% | ❌ POOR | Call graph has significant accuracy issues |

## Output Files

### 1. JSON Report

**Location**: `output/validation_reports/{Service}_{API}_validation.json`

**Contents**:
```json
{
  "success": true,
  "overall_accuracy": 98.5,
  "total_nodes": 156,
  "total_edges": 245,
  "method_coverage": {
    "coverage_percent": 100.0,
    "total_actual": 142,
    "total_in_graph": 142,
    "missing": [],
    "extra": []
  },
  "query_coverage": {
    "total_queries": 23,
    "nodes_with_queries": 18,
    "queries": [...]
  },
  "type_validation": {...},
  "parameter_validation": {...},
  "branch_validation": {...},
  "dao_validation": {...}
}
```

### 2. Text Report

**Location**: `output/validation_reports/{Service}_{API}_report.txt`

**Contents**: Human-readable summary with:
- Overall accuracy score
- Statistics (nodes, edges, queries, etc.)
- Missing methods (if any)
- Errors and warnings
- Branch coverage details
- DAO operation breakdown

## Common Issues and Solutions

### Issue: Low Method Coverage (<80%)

**Cause**: Call graph depth limit or internal methods not traced

**Solution**:
```bash
# Check config.py
CALL_GRAPH_MAX_NODES = None  # Should be None (unlimited)
CALL_GRAPH_TRACE_INTERNAL = True  # Should be True

# Clear cache and regenerate
curl -X DELETE http://localhost:8000/api/migration/cache
python test_api_validation.py ClaimService copyVisit
```

### Issue: Missing Queries

**Cause**: Queries in conditional branches not explored

**Solution**:
```bash
# Check config.py
CALL_GRAPH_TRACE_CONDITIONALS = True  # Should be True

# Enable debug mode
export DEBUG_CALL_GRAPH=true
python test_api_validation.py ClaimService copyVisit
```

### Issue: Return Type Mismatches

**Cause**: Complex return logic or generic types

**Solution**: Review the specific node in the JSON report and verify manually

### Issue: Missing DAO Operations

**Cause**: DAO methods not being traced

**Solution**:
```bash
# Verify DAO files exist
ls "c:\Users\pc\Desktop\trillium\af claims\allofactor\src\com\iris\allofactor\data\dao\impl"

# Check if DAO pattern matching works
export DEBUG_CALL_GRAPH=true
python test_api_validation.py ClaimService copyVisit
```

## Validation Workflow

### Step 1: Generate Call Graph
```bash
python test_api_validation.py ClaimService copyVisit
```

### Step 2: Review Results
```bash
# Check overall accuracy
cat output/validation_reports/ClaimService_copyVisit_report.txt

# Review JSON for details
cat output/validation_reports/ClaimService_copyVisit_validation.json
```

### Step 3: Fix Issues (if any)
```bash
# If accuracy < 95%, check:
# 1. Missing methods
# 2. Configuration settings
# 3. Java source file accessibility
```

### Step 4: Regenerate if Needed
```bash
# Clear cache
curl -X DELETE http://localhost:8000/api/migration/cache

# Regenerate with fixes
python test_api_validation.py ClaimService copyVisit
```

### Step 5: Verify 95%+ Accuracy
```bash
# Should see:
# ✅ EXCELLENT - Call graph is highly accurate
# Overall Accuracy: 98.5%
```

## Validation Checklist

Before using a call graph for migration, verify:

- [ ] Overall accuracy ≥ 95%
- [ ] Method coverage ≥ 95%
- [ ] All critical methods present (check missing list)
- [ ] All SQL/HQL queries captured
- [ ] All DAO operations included
- [ ] Conditional branches explored
- [ ] No critical errors in report
- [ ] Return types validated
- [ ] Parameters properly defined

## Advanced Usage

### Validate Multiple APIs

```bash
# Create a validation script
cat > validate_all.sh << 'EOF'
#!/bin/bash
apis=(
  "ClaimService copyVisit"
  "ClaimService getClaims"
  "EmrService getPatientData"
  "CalendarService getAppointments"
)

for api in "${apis[@]}"; do
  python test_api_validation.py $api
done
EOF

chmod +x validate_all.sh
./validate_all.sh
```

### Custom Validation Criteria

Edit `test_call_graph_accuracy.py` to adjust weights:

```python
# In _compile_results method
scores.append(method_coverage['coverage_percent'] * 0.5)  # Increase weight
scores.append(query_score * 0.3)  # Increase weight
```

### Export Validation Report

```bash
# Generate HTML report (requires pandoc)
pandoc output/validation_reports/ClaimService_copyVisit_report.txt \
  -o output/validation_reports/ClaimService_copyVisit_report.html
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Validate Call Graphs

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate copyVisit API
        run: python test_api_validation.py ClaimService copyVisit
      - name: Upload validation report
        uses: actions/upload-artifact@v2
        with:
          name: validation-reports
          path: output/validation_reports/
```

## Best Practices

1. **Always validate before migration** - Don't migrate with <95% accuracy
2. **Review missing methods** - Manually verify they're not critical
3. **Check query coverage** - Ensure all database operations are captured
4. **Validate return types** - Especially for complex DTOs
5. **Test with real data** - Compare actual API responses after migration
6. **Keep reports** - Archive validation reports for audit trail
7. **Automate validation** - Run on every call graph generation

## Troubleshooting

### Validation Script Fails to Run

```bash
# Check Python environment
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check Java files exist
ls "c:\Users\pc\Desktop\trillium\af claims\allofactorservice"
```

### "ModuleNotFoundError: No module named 'javalang'"

```bash
# Install javalang
pip install javalang

# Or install all dependencies
pip install -r requirements.txt
```

### Validation Takes Too Long

```bash
# For large APIs, this is normal
# Expected time: 30-60 seconds for complex APIs

# To speed up, reduce validation scope (not recommended)
# Edit test_call_graph_accuracy.py and comment out some checks
```

## Summary

The validation system ensures your call graphs are **accurate and complete** before migration. Always aim for:

- ✅ **95%+ overall accuracy**
- ✅ **100% method coverage** for critical paths
- ✅ **All queries captured**
- ✅ **All DAO operations included**

This guarantees your migrated Python API will behave **identically** to the Java API.

---

**Next Steps**: After validation passes, use the call graph for LLM-based code generation with confidence!
