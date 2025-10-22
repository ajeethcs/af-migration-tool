/**
 * Node-by-Node Migration Converter
 * 
 * Solves the "token too large" problem by converting one node at a time
 * instead of sending the entire call graph to the LLM at once.
 */

/**
 * Main function: Converts migration JSON to API configuration using node-by-node approach
 * 
 * @param migrationJson - The complete call graph from backend (with filtered metadata)
 * @returns Complete API configuration JSON
 */
export async function generateApiFromMigration(migrationJson: any): Promise<any> {
    if (!migrationJson) throw new Error('Migration JSON is empty');

    // Validate that metadata exists
    if (!migrationJson.metadata?.entities) {
        console.error('⚠️ Migration JSON missing metadata.entities!');
        throw new Error(
            'Migration JSON must include metadata.entities from BusinessLogicEnhancer. ' +
            'Ensure the backend is using the enhanced call graph.'
        );
    }

    // Log metadata stats
    const entityCount = Object.keys(migrationJson.metadata.entities || {}).length;
    const enumCount = Object.keys(migrationJson.metadata.enums || {}).length;
    const helperCount = Object.keys(migrationJson.metadata.helper_methods || {}).length;
    
    console.log('✓ Metadata validation passed:');
    console.log(`  - ${entityCount} entities with table/column mappings`);
    console.log(`  - ${enumCount} enums with value mappings`);
    console.log(`  - ${helperCount} helper method implementations`);

    // Convert node-by-node to avoid token limits
    console.log('\n🔄 Starting node-by-node conversion...');
    const apiConfig = await convertNodeByNode(migrationJson);
    
    console.log('✅ Conversion complete!');
    return apiConfig;
}

/**
 * Convert call graph node-by-node instead of all at once
 * This prevents token overflow by making multiple smaller LLM calls
 */
async function convertNodeByNode(migrationJson: any): Promise<any> {
    const nodes = migrationJson.nodes || [];
    const metadata = migrationJson.metadata || {};
    
    if (nodes.length === 0) {
        throw new Error('Call graph has no nodes!');
    }

    console.log(`\nTotal nodes to convert: ${nodes.length}`);
    console.log('Max tokens per call: ~30,000\n');

    const apiConfig = {
        name: migrationJson.api_name || 'unknown',
        active: true,
        nodes: {} as Record<string, any>,
        connections: {} as Record<string, any>
    };

    // Step 1: Convert API node (first node, no LLM needed)
    console.log('=' .repeat(70));
    console.log('STEP 1: Converting API Node');
    console.log('=' .repeat(70));
    
    apiConfig.nodes['__NODE1__'] = convertApiNode(nodes[0], migrationJson);
    console.log('✓ API node converted\n');

    // Step 2: Convert each code node individually
    for (let i = 1; i < nodes.length; i++) {
        const nodeNum = i + 1;
        const node = nodes[i];
        const nodeName = node.signature?.name || 'unknown';

        console.log('=' .repeat(70));
        console.log(`STEP ${nodeNum}: Converting Code Node - ${nodeName}`);
        console.log('=' .repeat(70));

        // Build minimal context for THIS node only
        const nodeContext = buildNodeContext(node, metadata, apiConfig);

        // Estimate tokens
        const estimatedTokens = estimateTokens(nodeContext);
        console.log(`  Estimated tokens: ${estimatedTokens.toLocaleString()}`);

        // Compress if needed
        if (estimatedTokens > 30000) {
            console.log('  ⚠️  Exceeds limit! Compressing...');
            compressContext(nodeContext);
            const compressedTokens = estimateTokens(nodeContext);
            console.log(`  Compressed tokens: ${compressedTokens.toLocaleString()}`);
        }

        // Convert this single node via LLM
        const converted = await convertSingleNode(nodeContext, nodeNum);

        apiConfig.nodes[`__NODE${nodeNum}__`] = converted;

        // Add connection from previous node
        const edgeId = `edge-__NODE${nodeNum - 1}__-__NODE${nodeNum}__`;
        apiConfig.connections[edgeId] = {
            id: edgeId,
            source: `__NODE${nodeNum - 1}__`,
            target: `__NODE${nodeNum}__`
        };

        console.log(`  ✓ Node ${nodeNum} converted\n`);
    }

    console.log('=' .repeat(70));
    console.log('CONVERSION COMPLETE');
    console.log('=' .repeat(70));
    console.log(`  Total nodes: ${Object.keys(apiConfig.nodes).length}`);
    console.log(`  Total connections: ${Object.keys(apiConfig.connections).length}`);
    console.log('=' .repeat(70) + '\n');

    return apiConfig;
}

/**
 * Build minimal context for converting a single node
 * Only includes metadata used in THIS specific node
 */
function buildNodeContext(
    node: any,
    fullMetadata: any,
    apiConfig: any
): any {
    const sourceCode = node.source_code || '';

    // Get only metadata used in THIS node
    const nodeMetadata = {
        entities: {} as Record<string, any>,
        enums: {} as Record<string, any>,
        helper_methods: {} as Record<string, any>,
        database: fullMetadata.database || { dialect: 'mysql' }
    };

    // Filter entities - only include those referenced in this node's source code
    for (const [entityName, entityData] of Object.entries(fullMetadata.entities || {})) {
        if (sourceCode.includes(entityName)) {
            nodeMetadata.entities[entityName] = entityData;
        }
    }

    // Filter enums - only include those referenced in this node's source code
    for (const [enumName, enumData] of Object.entries(fullMetadata.enums || {})) {
        if (sourceCode.includes(enumName)) {
            nodeMetadata.enums[enumName] = enumData;
        }
    }

    // Filter helpers - only include those called in this node's source code
    for (const [helperName, helperData] of Object.entries(fullMetadata.helper_methods || {})) {
        if (sourceCode.includes(helperName)) {
            nodeMetadata.helper_methods[helperName] = {
                signature: (helperData as any).signature || '',
                source_code: compressSourceCode((helperData as any).source_code || '')
            };
        }
    }

    // Build context with only essential information
    return {
        node: {
            name: node.signature?.name || 'unknown',
            signature: node.signature,
            source_code: compressSourceCode(sourceCode),
            node_type: node.node_type || 'code',
            logic_annotations: node.logic_annotations || {}
        },
        metadata: nodeMetadata,
        previous_nodes_summary: summarizePreviousNodes(apiConfig.nodes),
        conversion_hints: {
            critical_rules: fullMetadata.conversion_hints?.critical_rules || [
                'ALWAYS use metadata.entities for table/column lookups',
                'ALWAYS use metadata.enums for enum value lookups',
                'PRESERVE all business logic from Java',
                'Use parameterized queries for SQL injection prevention'
            ],
            database_dialect: fullMetadata.database?.dialect || 'mysql'
        }
    };
}

/**
 * Compress source code by removing comments and excessive whitespace
 */
function compressSourceCode(sourceCode: string): string {
    if (!sourceCode) return '';

    // Remove single-line comments
    sourceCode = sourceCode.replace(/\/\/.*$/gm, '');

    // Remove multi-line comments (but keep Javadoc)
    sourceCode = sourceCode.replace(/\/\*(?!\*)[\s\S]*?\*\//g, '');

    // Remove excessive whitespace
    sourceCode = sourceCode.replace(/\n\s*\n+/g, '\n');

    // Trim lines
    const lines = sourceCode
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

    return lines.join('\n');
}

/**
 * Create compact summary of previous nodes for context
 */
function summarizePreviousNodes(previousNodes: Record<string, any>): any[] {
    const summary = [];

    for (const [nodeId, nodeData] of Object.entries(previousNodes)) {
        summary.push({
            id: nodeId,
            name: nodeData.nodeName || 'unknown',
            type: nodeData.type || 'code',
            purpose: inferNodePurpose(nodeData)
        });
    }

    return summary;
}

/**
 * Infer the purpose of a node from its name/prompt
 */
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

/**
 * Estimate tokens (rough approximation: 1 token ≈ 4 characters)
 */
function estimateTokens(context: any): number {
    const jsonStr = JSON.stringify(context);
    return Math.floor(jsonStr.length / 4);
}

/**
 * Compress context further if it's too large
 */
function compressContext(context: any): void {
    // Simplify logic annotations
    if (context.node.logic_annotations) {
        const annotations = context.node.logic_annotations;
        context.node.logic_annotations = {
            complexity_score: annotations.complexity_score || 0,
            patterns: (annotations.patterns || []).map((p: any) => p.type || p),
            recommendations: (annotations.recommendations || []).slice(0, 3)
        };
    }

    // Compress helper source code if too long
    for (const helperData of Object.values(context.metadata.helper_methods || {})) {
        const helper = helperData as any;
        if (helper.source_code && helper.source_code.length > 500) {
            helper.source_code = helper.signature || '';
        }
    }

    // Limit previous nodes summary
    if (context.previous_nodes_summary && context.previous_nodes_summary.length > 5) {
        context.previous_nodes_summary = context.previous_nodes_summary.slice(-5);
    }
}

/**
 * Convert API node (no LLM needed, straightforward mapping)
 */
function convertApiNode(node: any, callGraph: any): any {
    const apiName = callGraph.api_name || 'unknown';
    const methodName = (node.signature?.name || '').toLowerCase();

    // Infer HTTP method from method name
    let httpMethod = 'POST';
    if (methodName.includes('get') || methodName.includes('find') || methodName.includes('search')) {
        httpMethod = 'GET';
    } else if (methodName.includes('update') || methodName.includes('modify')) {
        httpMethod = 'PUT';
    } else if (methodName.includes('delete') || methodName.includes('remove')) {
        httpMethod = 'DELETE';
    }

    // Extract parameters
    const params = (node.signature?.parameters || []).map((p: any) => ({
        key: p.name || '',
        value: getDefaultValue(p.type || '')
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
                apiDescription: `Migrated from Java SOAP service: ${callGraph.service_name || 'unknown'}`,
                queryParams: httpMethod === 'GET' ? params : [],
                formdataParams: httpMethod !== 'GET' ? params : [],
                headerParams: [],
                isAuthorizationEnabled: true,
                authentication: { credentialId: null },
                exceptionHandlers: [
                    {
                        exceptionCategoryId: 0,
                        name: 'All exceptions',
                        properties: {
                            errorMessage: 'An error occurred',
                            exceptionName: 'AllExceptions'
                        }
                    }
                ]
            }
        },
        nodeName: apiName,
        objectName: apiName.toLowerCase()
    };
}

/**
 * Get default value for parameter type
 */
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

/**
 * Convert a single node using LLM
 * This is where the actual LLM call happens (one node at a time)
 */
async function convertSingleNode(context: any, nodeNum: number): Promise<any> {
    const systemPrompt = getSingleNodePrompt();
    const apiKey = import.meta.env.VITE_OPENAI_API_KEY;

    if (!apiKey) {
        throw new Error('VITE_OPENAI_API_KEY is not set');
    }

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
                    content: `Convert this node to Python:\n\n${JSON.stringify(context, null, 2)}`
                }
            ]
        })
    });

    const data = await response.json();

    if (!response.ok) {
        const errMsg = data?.error?.message || 'Unknown error from OpenAI';
        throw new Error(`LLM API error: ${errMsg}`);
    }

    const raw = data?.choices?.[0]?.message?.content?.trim() || '{}';
    let result: any;
    
    try {
        result = JSON.parse(raw);
    } catch {
        throw new Error('Failed to parse LLM output as JSON: ' + raw);
    }

    // Add node metadata
    return {
        id: `__NODE${nodeNum}__`,
        type: 'code',
        position: { x: (nodeNum - 1) * 250, y: 150 },
        data: result.data || {
            label: 'Code',
            isLastNode: false,
            parameters: {
                language: 'python',
                prompt: result.prompt || 'Convert Java to Python',
                code: result.code || '# TODO: Conversion failed\npass'
            }
        },
        nodeName: result.nodeName || context.node.name || `node${nodeNum}`,
        objectName: result.objectName || (context.node.name || `node${nodeNum}`).toLowerCase()
    };
}

/**
 * Simplified system prompt for single node conversion
 * Much shorter than the full prompt to save tokens
 */
function getSingleNodePrompt(): string {
    return `You are converting a single Java method to a Python code node for a REST API.

CRITICAL RULES:
1. **Schema Lookups**: ALWAYS use metadata.entities for table/column name lookups
   - Java HQL: "from MediumClaim mc where mc.C_ID = :id"
   - Lookup: metadata.entities.MediumClaim.table_name → "CLAIM"
   - Lookup: metadata.entities.MediumClaim.fields.C_ID.column → "CLINIC_ID"
   - Python SQL: "SELECT * FROM CLAIM WHERE CLINIC_ID = :id"

2. **Enum Lookups**: ALWAYS use metadata.enums for enum value lookups
   - Java: Claim_ClaimStatus.CLAIMCREATED.getValue()
   - Lookup: metadata.enums.Claim_ClaimStatus.CLAIMCREATED → 2
   - Python: status == 2  # CLAIMCREATED

3. **Business Logic**: PRESERVE all if/else branches, validations, calculations

4. **Helper Methods**: If helpers are called, check metadata.helper_methods for implementations

5. **Database Queries**:
   - Use: db.execute(text('SELECT * FROM TABLE WHERE col = :param'), {'param': value})
   - Use .mappings().all() for multiple rows, .mappings().first() for single row
   - ALWAYS use parameterized queries

6. **Error Handling**:
   - Wrap in try/except
   - On success: return {"ok": True, "data": <result>}
   - On failure: return {"ok": False, "status": <code>, "message": "<msg>", "error": {"type": "<ErrorType>"}}

7. **Code Formatting**:
   - Use actual newlines (\\n) in the "code" field
   - Use 4 spaces for indentation
   - Format as: 'line1\\nline2\\nline3'

OUTPUT FORMAT (JSON only, no markdown):
{
  "data": {
    "label": "Code",
    "isLastNode": false,
    "parameters": {
      "language": "python",
      "prompt": "Brief description of what this node does",
      "code": "from sqlalchemy import text\\ntry:\\n    # Your Python code here\\n    pass\\nexcept Exception as e:\\n    return {\\"ok\\": False, \\"status\\": 500, \\"message\\": str(e)}"
    }
  },
  "nodeName": "descriptive_node_name",
  "objectName": "descriptive_node_name"
}

IMPORTANT: Return ONLY valid JSON. No explanations, no markdown, no code fences.`;
}

// Export for use in other modules
export { convertNodeByNode, buildNodeContext, convertSingleNode };
