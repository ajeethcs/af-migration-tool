# Quick Start - Complete Call Graph Mode

## 🚀 3-Step Setup

### 1️⃣ Test the Changes
```bash
cd "c:\Users\pc\Desktop\trillium\af claims\migration-tool"
python test_complete_mode.py
```

**Expected**: `✅ SUCCESS: Call graph is COMPLETE!`

### 2️⃣ Clear Cache & Restart Server
```bash
# Terminal 1: Start server
python -m uvicorn main:app --reload

# Terminal 2: Clear cache
curl -X DELETE http://localhost:8000/api/migration/cache
```

### 3️⃣ Regenerate copyVisit Call Graph
```bash
curl -X POST http://localhost:8000/api/migration/start \
  -H "Content-Type: application/json" \
  -d "{\"service_name\": \"ClaimService\", \"api_name\": \"copyVisit\", \"llm_model\": \"gpt-4\"}"
```

## ✅ Verification Checklist

Open the generated JSON and verify these nodes exist:

```
□ ClaimServiceImpl.copyVisit
□ DaoFacadeImpl.saveCopyClaimByCopyVisitParams
□ ClaimInfoBODaoImpl.saveCopyClaimByCopyVisitParams
□ ClaimInfoBODaoImpl.getCopyClaimInfoBO ← CRITICAL
□ ClaimInfoBODaoImpl.storeOrUpdateCopyClaimInfoBO ← CRITICAL
□ VisitDiagnosisAndProcedureBODaoImpl.getCopyVisitDiagnosisAndProcedure
□ ProvidersAndFacilityDao.getProvidersAndFacilityByVisitId
□ MiscellaneousBODaoImpl.getMiscellaneousByVisitId
□ CMSOverrideDataDao.getCMSOverrideDataByVisitId
```

**If all checked**: ✅ Call graph is complete!
**If some missing**: ⚠️ See troubleshooting below

## 🔍 Quick Verification

```bash
# Check node count (should be 100+)
cat output/call_graphs/<migration_id>.json | grep '"id":' | wc -l

# Check for critical method
cat output/call_graphs/<migration_id>.json | grep 'getCopyClaimInfoBO'
```

## 🐛 Troubleshooting

### Issue: Test fails
```bash
# Check Java files exist
ls "c:\Users\pc\Desktop\trillium\af claims\allofactorservice\src\com\iris\allofactor\services\impl\ClaimServiceImpl.java"

# Check config paths
python -c "from config import *; print(SERVICES_IMPL_PATH)"
```

### Issue: Call graph incomplete
```bash
# 1. Clear cache
curl -X DELETE http://localhost:8000/api/migration/cache

# 2. Restart server (Ctrl+C then restart)
python -m uvicorn main:app --reload

# 3. Enable debug mode
export DEBUG_CALL_GRAPH=true
python -m uvicorn main:app --reload

# 4. Regenerate
curl -X POST http://localhost:8000/api/migration/start ...
```

### Issue: "Too many nodes"
**This is CORRECT!** Complete tracing should produce 100-200+ nodes.

## 📊 Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Nodes | 20-30 | 100-200+ |
| Size | 25 KB | 500 KB - 2 MB |
| Time | 2-5 sec | 10-30 sec |
| Coverage | 20-25% | **100%** |

## 🎯 Success Criteria

✅ Test script passes
✅ All checklist items present
✅ Node count > 100
✅ File size > 500 KB
✅ Contains `getCopyClaimInfoBO` and `storeOrUpdateCopyClaimInfoBO`

## 📚 More Info

- **Complete Guide**: `COMPLETE_CALL_GRAPH_MODE.md`
- **Changes Summary**: `CHANGES_SUMMARY.md`
- **Test Script**: `test_complete_mode.py`

---

**Need Help?** Check the troubleshooting section or review the complete documentation.
