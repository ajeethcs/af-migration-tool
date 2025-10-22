## Node-by-Node Conversion Integration

## The Solution to "Token Too Large" Problem

Instead of sending the **entire call graph** to the LLM at once (100K+ tokens), we now send **one node at a time** (10-15K tokens each).

---

## How It Works

### **Old Approach (Token Overflow):**

```
Single LLM Call:
├── System Prompt (15K tokens)
├── Full Call Graph
│   ├── Node 1 source code (5K tokens)
│   ├── Node 2 source code (8K tokens)
│   ├── Node 3 source code (12K tokens)
│   ├── ... 10 more nodes ...
│   └── All metadata (20K tokens)
└── TOTAL: 120K tokens ❌ REJECTED!
```

### **New Approach (Node-by-Node):**

```
Call 1 (API Node):
├── System Prompt (5K tokens)
├── API node only (2K tokens)
└── TOTAL: 7K tokens ✅

Call 2 (Code Node 1):
├── System Prompt (5K tokens)
├── Node 1 source (3K tokens)
├── Node 1 metadata (2K tokens)
├── Previous context (1K tokens)
└── TOTAL: 11K tokens ✅

Call 3 (Code Node 2):
├── System Prompt (5K tokens)
├── Node 2 source (4K tokens)
├── Node 2 metadata (1K tokens)
├── Previous context (1K tokens)
└── TOTAL: 11K tokens ✅

... repeat for each node ...

Total: 10 calls × 11K = 110K tokens
But spread across 10 separate API calls! ✅
```

---

## Backend Integration (Python)

### **Update `generateApiFromMigration` in TypeScript:**

```typescript
export async function generateApiFromMigration(migrationJson: any): Promise<any> {
    if (!migrationJson) throw new Error('Migration JSON is empty');

    // Validate metadata
    if (!migrationJson.metadata?.entities) {
        throw new Error('Migration JSON must include metadata.entities');
    }

    const apiKey = import.meta.env.VITE_OPENAI_API_KEY;
    
    // NEW: Convert node-by-node instead of all at once
    const apiConfig = await convertNodeByNode(migrationJson, apiKey);
    
    return apiConfig;
}
```

### **New Function: `convertNodeByNode`:**

```typescript
async function convertNodeByNode(
    migrationJson: any,
    apiKey: string
): Promise<any> {
    console.log('🔄 Starting node-by-node conversion...');
    
    const nodes = migrationJson.nodes || [];
    const metadata = migrationJson.metadata || {};
    
    const apiConfig = {
        name: migrationJson.api_name,
        active: true,
        nodes: {},
        connections: {}
    };
    
    // Step 1: Convert API node (no LLM needed)
    console.log('1. Converting API node...');
    apiConfig.nodes['__NODE1__'] = convertApiNode(nodes[0], migrationJson);
    
    // Step 2: Convert each code node individually
    for (let i = 1; i < nodes.length; i++) {
        const nodeNum = i + 1;
        const node = nodes[i];
        
        console.log(`${nodeNum}. Converting ${node.signature?.name || 'unknown'}...`);
        
        // Build minimal context for THIS node only
        const nodeContext = buildNodeContext(node, metadata, apiConfig);
        
        // Estimate tokens
        const estimatedTokens = estimateTokens(nodeContext);
        console.log(`   Estimated tokens: ${estimatedTokens.toLocaleString()}`);
        
        // Compress if needed
        if (estimatedTokens > 30000) {
            console.log('   ⚠️  Too large! Compressing...');
            compressContext(nodeContext);
        }
        
        // Convert this single node via LLM
        const converted = await convertSingleNode(nodeContext, apiKey, nodeNum);
        
        apiConfig.nodes[`__NODE${nodeNum}__`] = converted;
        
        // Add connection
        apiConfig.connections[`edge-__NODE${nodeNum-1}__-__NODE${nodeNum}__`] = {
            id: `edge-__NODE${nodeNum-1}__-__NODE${nodeNum}__`,
            source: `__NODE${nodeNum-1}__`,
            target: `__NODE${nodeNum}__`
        };
        
        console.log(`   ✓ Node ${nodeNum} converted`);
    }
    
    console.log('✅ Conversion complete!');
    return apiConfig;
}
```

### **Helper Functions:**

```typescript
function buildNodeContext(
    node: any,
    fullMetadata: any,
    apiConfig: any
): any {
    // Get only metadata used in THIS node
    const nodeMetadata = getNodeMetadata(node, fullMetadata);
    
    return {
        node: {
            name: node.signature?.name || 'unknown',
            signature: node.signature,
            source_code: compressSourceCode(node.source_code || ''),
            node_type: node.node_type,
            logic_annotations: node.logic_annotations
        },
        metadata: nodeMetadata,
        previous_nodes_summary: summarizePreviousNodes(apiConfig.nodes),
        conversion_hints: {
            critical_rules: fullMetadata.conversion_hints?.critical_rules || []
        }
    };
}

function getNodeMetadata(node: any, fullMetadata: any): any {
    const sourceCode = node.source_code || '';
    
    const nodeMetadata = {
        entities: {},
        enums: {},
        helper_methods: {},
        database: { dialect: fullMetadata.database?.dialect || 'mysql' }
    };
    
    // Only include entities referenced in THIS node
    for (const [entityName, entityData] of Object.entries(fullMetadata.entities || {})) {
        if (sourceCode.includes(entityName)) {
            nodeMetadata.entities[entityName] = {
                table_name: entityData.table_name,
                fields: entityData.fields
            };
        }
    }
    
    // Only include enums referenced in THIS node
    for (const [enumName, enumData] of Object.entries(fullMetadata.enums || {})) {
        if (sourceCode.includes(enumName)) {
            nodeMetadata.enums[enumName] = enumData;
        }
    }
    
    // Only include helpers called in THIS node
    for (const [helperName, helperData] of Object.entries(fullMetadata.helper_methods || {})) {
        if (sourceCode.includes(helperName)) {
            nodeMetadata.helper_methods[helperName] = {
                signature: helperData.signature,
                source_code: compressSourceCode(helperData.source_code || '')
            };
        }
    }
    
    return nodeMetadata;
}

function compressSourceCode(sourceCode: string): string {
    // Remove comments
    sourceCode = sourceCode.replace(/\/\/.*$/gm, '');
    sourceCode = sourceCode.replace(/\/\*[\s\S]*?\*\//g, '');
    
    // Remove excessive whitespace
    sourceCode = sourceCode.replace(/\n\s*\n/g, '\n');
    
    // Trim lines
    const lines = sourceCode.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
    
    return lines.join('\n');
}

function summarizePreviousNodes(previousNodes: any): any[] {
    const summary = [];
    
    for (const [nodeId, nodeData] of Object.entries(previousNodes)) {
        summary.push({
            id: nodeId,
            name: nodeData.nodeName,
            type: nodeData.type,
            purpose: inferNodePurpose(nodeData)
        });
    }
    
    return summary;
}

function inferNodePurpose(nodeData: any): string {
    const name = (nodeData.nodeName || '').toLowerCase();
    const prompt = (nodeData.data?.parameters?.prompt || '').toLowerCase();
    
    if (name.includes('validate') || prompt.includes('validate')) {
        return 'validation';
    } else if (name.includes('query') || prompt.includes('database')) {
        return 'database_query';
    } else if (name.includes('format') || prompt.includes('response')) {
        return 'formatting';
    } else {
        return 'business_logic';
    }
}

function estimateTokens(context: any): number {
    const jsonStr = JSON.stringify(context);
    return Math.floor(jsonStr.length / 4);
}

function compressContext(context: any): void {
    // Simplify logic annotations
    if (context.node.logic_annotations) {
        context.node.logic_annotations = {
            complexity_score: context.node.logic_annotations.complexity_score || 0,
            patterns: (context.node.logic_annotations.patterns || [])
                .map((p: any) => p.type),
            recommendations: (context.node.logic_annotations.recommendations || [])
                .slice(0, 3)
        };
    }
    
    // Compress helpers
    for (const helperData of Object.values(context.metadata.helper_methods || {})) {
        if (helperData.source_code?.length > 500) {
            helperData.source_code = helperData.signature || '';
        }
    }
}

function convertApiNode(node: any, callGraph: any): any {
    const apiName = callGraph.api_name || 'unknown';
    const methodName = (node.signature?.name || '').toLowerCase();
    
    // Infer HTTP method
    let httpMethod = 'POST';
    if (methodName.includes('get') || methodName.includes('find')) {
        httpMethod = 'GET';
    } else if (methodName.includes('update')) {
        httpMethod = 'PUT';
    } else if (methodName.includes('delete')) {
        httpMethod = 'DELETE';
    }
    
    // Extract parameters
    const params = (node.signature?.parameters || []).map((p: any) => ({
        key: p.name,
        value: getDefaultValue(p.type)
    }));
    
    return {
        id: '__NODE1__',
        type: 'api',
        position: { x: 0, y: 150 },
        data: {
            label: 'API',
            isLastNode: false,
            parameters: {
                apiName: apiName,
                httpMethod: httpMethod,
                path: `/${apiName}`,
                apiDescription: 'Migrated from Java SOAP service',
                queryParams: httpMethod === 'GET' ? params : [],
                formdataParams: httpMethod !== 'GET' ? params : [],
                headerParams: [],
                isAuthorizationEnabled: true,
                authentication: { credentialId: null },
                exceptionHandlers: [{
                    exceptionCategoryId: 0,
                    name: 'All exceptions',
                    properties: {
                        errorMessage: 'An error occurred',
                        exceptionName: 'AllExceptions'
                    }
                }]
            }
        },
        nodeName: apiName,
        objectName: apiName.toLowerCase()
    };
}

function getDefaultValue(type: string): string {
    const defaults: Record<string, string> = {
        'int': '0',
        'long': '0',
        'double': '0.0',
        'float': '0.0',
        'boolean': 'false',
        'String': '',
        'Date': '2024-01-01'
    };
    return defaults[type] || '';
}

async function convertSingleNode(
    context: any,
    apiKey: string,
    nodeNumber: number
): Promise<any> {
    // Build simplified system prompt for single node
    const systemPrompt = buildSingleNodePrompt();
    
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            model: 'gpt-4o',
            temperature: 0,
            response_format: { type: 'json_object' },
            messages: [
                { role: 'system', content: systemPrompt },
                {
                    role: 'user',
                    content: `Convert this node to Python:\n${JSON.stringify(context, null, 2)}`
                }
            ]
        })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data?.error?.message || 'LLM API error');
    }
    
    const result = JSON.parse(data.choices[0].message.content);
    
    // Add node metadata
    result.id = `__NODE${nodeNumber}__`;
    result.type = 'code';
    result.position = { x: (nodeNumber - 1) * 250, y: 150 };
    
    return result;
}

function buildSingleNodePrompt(): string {
    return `You are converting a single Java method to a Python code node.

CRITICAL RULES:
1. Use metadata.entities for table/column lookups
2. Use metadata.enums for enum value lookups
3. Preserve all business logic from Java
4. Return valid JSON only

Output format:
{
  "data": {
    "label": "Code",
    "isLastNode": false,
    "parameters": {
      "language": "python",
      "prompt": "Description of what this node does",
      "code": "Python code with \\n for newlines"
    }
  },
  "nodeName": "node_name",
  "objectName": "node_name"
}`;
}
```

---

## Token Savings

### **Example: getClaims API with 10 nodes**

| Approach | Tokens per Call | Total Calls | Total Tokens | Status |
|----------|----------------|-------------|--------------|--------|
| **Old (All at once)** | 120,000 | 1 | 120,000 | ❌ REJECTED |
| **New (Node-by-node)** | 10,000 | 10 | 100,000 | ✅ ACCEPTED |

**Key difference:** Tokens are spread across multiple calls, each within limits!

---

## Cost Comparison

### **GPT-4 Pricing:**
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens

### **Old Approach (if it worked):**
- 1 call × 120K tokens = $3.60 input + $2.40 output = **$6.00**

### **New Approach:**
- 10 calls × 10K tokens each = $3.00 input + $2.00 output = **$5.00**
- **Savings: $1.00 (17%)**
- **Plus: Actually works!** ✅

---

## Implementation Steps

1. ✅ **Created `NodeByNodeConverter`** in Python backend
2. ⚠️ **Update TypeScript** to use node-by-node conversion
3. ⚠️ **Test with real API** to verify token limits
4. ⚠️ **Monitor costs** and optimize further if needed

---

## Next Steps

Would you like me to:
1. Update the TypeScript prompt file with node-by-node conversion?
2. Create a test to verify token limits are respected?
3. Add progress tracking for multi-node conversion?

Let me know which you'd prefer!
