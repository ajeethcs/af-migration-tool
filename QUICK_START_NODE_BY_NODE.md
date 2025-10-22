# Quick Start: Node-by-Node Conversion

## TL;DR - The Solution

**Problem:** Sending entire call graph to LLM = 100K+ tokens → API rejected  
**Solution:** Send one node at a time = 10-15K tokens per call → All accepted ✅

---

## 3-Step Setup

### **Step 1: Update Your Import**

```typescript
// In your UI code (e.g., MigrationComponent.tsx or wherever you call the LLM)

// ❌ OLD
// import { generateApiFromMigration } from './UPDATED_TYPESCRIPT_PROMPT';

// ✅ NEW
import { generateApiFromMigration } from './UPDATED_TYPESCRIPT_PROMPT_NODE_BY_NODE';
```

### **Step 2: Use It (No Code Changes!)**

```typescript
// Your existing code works as-is!
const callGraph = await fetch('/api/migration/call-graph/abc-123');
const apiConfig = await generateApiFromMigration(callGraph);
```

### **Step 3: Done!**

That's it! The function automatically:
- Converts one node at a time
- Estimates tokens before sending
- Compresses if needed
- Shows progress in console

---

## What You'll See

### **Console Output:**

```
✓ Metadata validation passed:
  - 3 entities, 2 enums, 3 helpers

🔄 Starting node-by-node conversion...
Total nodes to convert: 6

STEP 1: Converting API Node
✓ API node converted

STEP 2: Converting Code Node - validateInput
  Estimated tokens: 8,234
  ✓ Node 2 converted

STEP 3: Converting Code Node - buildQuery
  Estimated tokens: 12,456
  ✓ Node 3 converted

STEP 4: Converting Code Node - executeQuery
  Estimated tokens: 35,678
  ⚠️  Exceeds limit! Compressing...
  Compressed tokens: 14,567
  ✓ Node 4 converted

✅ Conversion complete!
```

---

## Token Savings

| Approach | Tokens | Status |
|----------|--------|--------|
| **Old (all at once)** | 95,000 | ❌ REJECTED |
| **New (node-by-node)** | 10,000 per call | ✅ ACCEPTED |

---

## Backend Changes

**None!** The Python backend already does everything correctly:

```python
# api/routes/api_migration.py (ALREADY CORRECT!)
enhanced_graph = enhancer.enhance_call_graph(
    call_graph.model_dump(),
    filter_metadata=True  # ✅ Already filtering
)
return enhanced_graph  # UI handles node-by-node conversion
```

---

## Files

- **`UPDATED_TYPESCRIPT_PROMPT_NODE_BY_NODE.ts`** - Use this file
- **`HOW_TO_USE_NODE_BY_NODE.md`** - Detailed guide
- **`TOKEN_PROBLEM_SOLUTION.md`** - Complete explanation

---

## Summary

✅ **Update import** → Use `UPDATED_TYPESCRIPT_PROMPT_NODE_BY_NODE.ts`  
✅ **No code changes** → Same function signature  
✅ **No backend changes** → Already correct  
✅ **Problem solved** → No more token rejections  

Done! 🎉
