# Solutions for Large Call Graph Migration

## Problem

The `copyVisit` API call graph exceeds token limits:
- **Call graph size**: 337,803 tokens
- **Model limit (gpt-5-mini)**: 272,000 tokens
- **Overflow**: 65,803 tokens (24% over)

## ⚠️ Why We CANNOT Prune Source Code

**Source code is CRITICAL for faithful migration because:**

1. ✅ **Complete Business Logic** - Shows all conditional branches, loops, transformations
2. ✅ **Variable Names** - Preserves exact naming for response structure
3. ✅ **Data Flow** - Shows how data moves through the system
4. ✅ **Error Handling** - Shows all try-catch blocks and error cases
5. ✅ **Edge Cases** - Shows special handling for null, empty, edge conditions
6. ✅ **Comments** - May contain important business rules
7. ✅ **Context** - LLM needs full context to avoid hallucination

**Without source code, the LLM will:**
- ❌ Hallucinate business logic
- ❌ Miss edge cases
- ❌ Incorrectly handle nulls/empties
- ❌ Generate incomplete implementations
- ❌ Break response structure compatibility

---

## ✅ **Solution 1: Use Larger Context Window Model** (RECOMMENDED)

### **Option A: GPT-4o (128k tokens)**

**Context Window**: 128,000 tokens (47% larger than gpt-5-mini)

**Configuration**:
```typescript
model: 'gpt-4o',
temperature: 0,  // Deterministic output
```

**Pros**:
- ✅ 128k context window (vs 272k needed)
- ✅ Better code generation quality
- ✅ More accurate migrations
- ✅ Supports JSON mode

**Cons**:
- ⚠️ Still might not fit (337k tokens > 128k)
- ⚠️ Higher cost than gpt-5-mini

**Status**: ⚠️ May still exceed limit for very large APIs

---

### **Option B: GPT-4 Turbo (128k tokens)**

**Context Window**: 128,000 tokens

**Configuration**:
```typescript
model: 'gpt-4-turbo',
temperature: 0,
```

**Pros**:
- ✅ Same as GPT-4o
- ✅ Proven reliability

**Cons**:
- ⚠️ Same limitations as GPT-4o

**Status**: ⚠️ May still exceed limit

---

### **Option C: Claude 3.5 Sonnet (200k tokens)** (BEST FOR LARGE APIS)

**Context Window**: 200,000 tokens (73% of what you need)

**Configuration**:
```typescript
// Switch to Anthropic API
const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': anthropicApiKey,
        'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 4096,
        temperature: 0,
        system: systemPrompt,
        messages: [
            { role: 'user', content: jsonString }
        ]
    })
});
```

**Pros**:
- ✅ 200k context window (largest available)
- ✅ Excellent code generation
- ✅ Better at following complex instructions
- ✅ More likely to fit large call graphs

**Cons**:
- ⚠️ Still might not fit (337k > 200k)
- ⚠️ Requires Anthropic API key
- ⚠️ Different API format

**Status**: ⚠️ Closer but may still exceed for very large APIs

---

### **Option D: Gemini 1.5 Pro (1M tokens)** (BEST FOR VERY LARGE APIS)

**Context Window**: 1,000,000 tokens (3x what you need!)

**Configuration**:
```typescript
// Switch to Google AI API
const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': googleApiKey
    },
    body: JSON.stringify({
        contents: [{
            parts: [{
                text: systemPrompt + '\n\n' + jsonString
            }]
        }],
        generationConfig: {
            temperature: 0,
            responseMimeType: 'application/json'
        }
    })
});
```

**Pros**:
- ✅ 1M context window (will definitely fit!)
- ✅ Can handle even the largest APIs
- ✅ Good code generation
- ✅ Cost-effective for large contexts

**Cons**:
- ⚠️ Requires Google AI API key
- ⚠️ Different API format
- ⚠️ May need prompt adjustments

**Status**: ✅ **WILL FIT** - Recommended for large APIs

---

## ✅ **Solution 2: Chunking Strategy** (ALTERNATIVE)

If you must use smaller context models, split the migration into chunks.

### **Strategy: Split by Functional Areas**

**Example for copyVisit**:

**Chunk 1: Core Visit Copy Logic**
- Entry point: `copyVisit`
- Main orchestration: `saveCopyClaimByCopyVisitParams`
- Core data: `getCopyClaimInfoBO`, `storeOrUpdateCopyClaimInfoBO`

**Chunk 2: Diagnosis & Procedures**
- `getCopyVisitDiagnosisAndProcedure`
- `storeOrUpdateCopyVisitDiagnosisAndProcedure`
- Related DAO methods

**Chunk 3: Providers & Facility**
- `getProvidersAndFacilityByVisitId`
- `storeOrUpdateProvidersAndFacility`
- Related DAO methods

**Chunk 4: Miscellaneous & CMS**
- `getMiscellaneousByVisitId`
- `getCMSOverrideDataByVisitId`
- `storeOrUpdateMiscellaneous`
- `storeOrUpdateCMSOverrideData`

### **Implementation**:

```typescript
async function generateApiInChunks(fullMigrationJson: any): Promise<any> {
    // 1. Split call graph into functional chunks
    const chunks = splitCallGraphByFunctionalArea(fullMigrationJson);
    
    // 2. Generate scaffold for each chunk
    const chunkResults = [];
    for (const chunk of chunks) {
        const result = await generateApiFromMigration(chunk);
        chunkResults.push(result);
    }
    
    // 3. Merge chunks into single API
    const mergedApi = mergeChunkResults(chunkResults);
    
    return mergedApi;
}
```

**Pros**:
- ✅ Works with any model
- ✅ Can handle unlimited size

**Cons**:
- ❌ Complex to implement
- ❌ Risk of inconsistency between chunks
- ❌ May lose cross-chunk context
- ❌ Harder to maintain execution flow

---

## ✅ **Solution 3: Optimize Call Graph Generation** (PREVENTIVE)

Reduce call graph size at generation time.

### **Strategy: Selective Tracing**

**In `config.py`**:
```python
# Trace only critical paths
CALL_GRAPH_TRACE_HELPERS = False  # Skip helper methods
CALL_GRAPH_TRACE_GETTERS_SETTERS = False  # Skip simple getters/setters
CALL_GRAPH_MAX_DEPTH = 10  # Limit depth to critical methods
```

**Pros**:
- ✅ Smaller call graphs
- ✅ Faster generation

**Cons**:
- ❌ May miss important logic
- ❌ Less complete migration
- ❌ Not recommended for faithful migration

---

## 📊 **Comparison Table**

| Solution | Context Window | Will Fit? | Quality | Complexity | Cost |
|----------|---------------|-----------|---------|------------|------|
| **GPT-4o** | 128k | ⚠️ Maybe | ⭐⭐⭐⭐⭐ | Low | $$ |
| **GPT-4 Turbo** | 128k | ⚠️ Maybe | ⭐⭐⭐⭐⭐ | Low | $$ |
| **Claude 3.5 Sonnet** | 200k | ⚠️ Likely | ⭐⭐⭐⭐⭐ | Medium | $$ |
| **Gemini 1.5 Pro** | 1M | ✅ Yes | ⭐⭐⭐⭐ | Medium | $ |
| **Chunking** | Any | ✅ Yes | ⭐⭐⭐ | High | $ |
| **Optimize Graph** | Any | ✅ Yes | ⭐⭐ | Low | $ |

---

## 🎯 **Recommended Approach**

### **For Your Use Case (337k tokens)**:

**Primary Recommendation**: **Gemini 1.5 Pro**
- ✅ 1M context window (will definitely fit)
- ✅ Cost-effective
- ✅ Good quality
- ✅ Simple implementation

**Fallback**: **Claude 3.5 Sonnet** + **Chunking**
- ✅ 200k context (may fit with minor optimization)
- ✅ Excellent quality
- ✅ Can chunk if needed

---

## 🔧 **Implementation: Gemini 1.5 Pro**

### **Step 1: Install Google AI SDK**

```bash
npm install @google/generative-ai
```

### **Step 2: Add API Key**

```bash
# .env
VITE_GOOGLE_AI_API_KEY=your_api_key_here
```

### **Step 3: Update migrationPrompt.ts**

```typescript
import { GoogleGenerativeAI } from '@google/generative-ai';

export async function generateApiFromMigrationGemini(fullMigrationJson: any): Promise<any> {
    if (!fullMigrationJson) throw new Error('Migration JSON is empty');
    if (!fullMigrationJson.metadata?.entities) {
        throw new Error('Migration JSON must include metadata.entities.');
    }

    const systemPrompt = getApiMigrationScaffoldPrompt();
    const jsonString = JSON.stringify(fullMigrationJson);

    console.log(`JSON size: ${jsonString.length} characters`);
    console.log(`Estimated tokens: ~${Math.ceil(jsonString.length / 4)}`);

    const apiKey = import.meta.env.VITE_GOOGLE_AI_API_KEY;
    if (!apiKey) throw new Error('Google AI API key not found');

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ 
        model: 'gemini-1.5-pro',
        generationConfig: {
            temperature: 0,
            responseMimeType: 'application/json'
        }
    });

    console.log('Sending request to Gemini 1.5 Pro...');

    const prompt = `${systemPrompt}\n\n### MIGRATION JSON:\n${jsonString}`;
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    let scaffoldJson: any;
    try {
        scaffoldJson = JSON.parse(text);
    } catch (e) {
        console.error('Failed to parse Gemini output as JSON:', text);
        throw new Error('Failed to parse response: ' + (e as Error).message);
    }

    console.log('Successfully generated scaffold');
    return scaffoldJson;
}
```

---

## 🔧 **Implementation: Claude 3.5 Sonnet**

### **Step 1: Install Anthropic SDK**

```bash
npm install @anthropic-ai/sdk
```

### **Step 2: Add API Key**

```bash
# .env
VITE_ANTHROPIC_API_KEY=your_api_key_here
```

### **Step 3: Update migrationPrompt.ts**

```typescript
import Anthropic from '@anthropic-ai/sdk';

export async function generateApiFromMigrationClaude(fullMigrationJson: any): Promise<any> {
    if (!fullMigrationJson) throw new Error('Migration JSON is empty');
    if (!fullMigrationJson.metadata?.entities) {
        throw new Error('Migration JSON must include metadata.entities.');
    }

    const systemPrompt = getApiMigrationScaffoldPrompt();
    const jsonString = JSON.stringify(fullMigrationJson);

    console.log(`JSON size: ${jsonString.length} characters`);

    const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
    if (!apiKey) throw new Error('Anthropic API key not found');

    const anthropic = new Anthropic({ apiKey });

    console.log('Sending request to Claude 3.5 Sonnet...');

    const message = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 4096,
        temperature: 0,
        system: systemPrompt,
        messages: [{
            role: 'user',
            content: `### MIGRATION JSON:\n${jsonString}`
        }]
    });

    const text = message.content[0].type === 'text' 
        ? message.content[0].text 
        : '';

    let scaffoldJson: any;
    try {
        scaffoldJson = JSON.parse(text);
    } catch (e) {
        console.error('Failed to parse Claude output as JSON:', text);
        throw new Error('Failed to parse response: ' + (e as Error).message);
    }

    console.log('Successfully generated scaffold');
    return scaffoldJson;
}
```

---

## 📋 **Quick Decision Guide**

### **Choose Gemini 1.5 Pro if:**
- ✅ Your call graph is > 200k tokens
- ✅ You want guaranteed fit
- ✅ You want cost-effective solution
- ✅ You're okay with Google AI API

### **Choose Claude 3.5 Sonnet if:**
- ✅ Your call graph is 150k-200k tokens
- ✅ You want best quality
- ✅ You prefer Anthropic
- ✅ You can chunk if needed

### **Choose GPT-4o if:**
- ✅ Your call graph is < 100k tokens
- ✅ You want to stay with OpenAI
- ✅ You want JSON mode
- ✅ You're already using OpenAI

### **Use Chunking if:**
- ✅ You must use a specific model
- ✅ Context window is too small
- ✅ You can handle complexity
- ✅ You can ensure consistency

---

## ✅ **Current Configuration**

I've updated your `migrationPrompt.ts` to use **GPT-4o** (128k context) as an intermediate solution.

**Next steps**:

1. **Try GPT-4o first** - May fit with 128k context
2. **If still too large** - Switch to Gemini 1.5 Pro (1M context)
3. **If quality issues** - Switch to Claude 3.5 Sonnet (200k context)

---

**Remember**: Source code is NON-NEGOTIABLE for faithful migration. Always preserve complete source code to avoid hallucination and ensure accurate business logic implementation.
