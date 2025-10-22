/**
 * Complete usage example for the updated migration prompt
 */

import { generateApiFromMigration } from './UPDATED_TYPESCRIPT_PROMPT';

// ============================================================================
// EXAMPLE 1: Basic Usage
// ============================================================================

async function basicExample() {
    // 1. Get call graph from backend
    const response = await fetch('http://localhost:8000/api/migration/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            service_name: 'ClaimService',
            api_name: 'getClaims'
        })
    });

    const callGraph = await response.json();

    // 2. Generate API configuration (that's it!)
    const apiConfig = await generateApiFromMigration(callGraph);

    console.log('Generated API:', apiConfig);
}

// ============================================================================
// EXAMPLE 2: With Error Handling
// ============================================================================

async function withErrorHandling() {
    try {
        const response = await fetch('http://localhost:8000/api/migration/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                service_name: 'ClaimService',
                api_name: 'getClaims'
            })
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.statusText}`);
        }

        const callGraph = await response.json();

        // Validate call graph structure
        if (!callGraph.metadata) {
            throw new Error('Call graph missing metadata - backend may not be using BusinessLogicEnhancer');
        }

        // Generate API
        const apiConfig = await generateApiFromMigration(callGraph);

        return apiConfig;

    } catch (error) {
        if (error.message.includes('metadata.entities')) {
            console.error('❌ Backend is not using BusinessLogicEnhancer!');
            console.error('Fix: Update backend to enhance call graph before returning');
        } else {
            console.error('❌ Migration failed:', error);
        }
        throw error;
    }
}

// ============================================================================
// EXAMPLE 3: Batch Processing Multiple APIs
// ============================================================================

async function batchMigration(apis: Array<{ service: string; api: string }>) {
    const results = [];

    for (const { service, api } of apis) {
        try {
            console.log(`\n🔄 Processing ${service}.${api}...`);

            // Get call graph
            const response = await fetch('http://localhost:8000/api/migration/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    service_name: service,
                    api_name: api
                })
            });

            const callGraph = await response.json();

            // Generate API
            const apiConfig = await generateApiFromMigration(callGraph);

            results.push({
                service,
                api,
                status: 'success',
                config: apiConfig
            });

            console.log(`✅ ${service}.${api} completed`);

        } catch (error) {
            console.error(`❌ ${service}.${api} failed:`, error.message);
            results.push({
                service,
                api,
                status: 'failed',
                error: error.message
            });
        }
    }

    return results;
}

// ============================================================================
// EXAMPLE 4: With Validation and Logging
// ============================================================================

async function withValidation() {
    const response = await fetch('http://localhost:8000/api/migration/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            service_name: 'ClaimService',
            api_name: 'getClaims'
        })
    });

    const callGraph = await response.json();

    // Validate call graph structure
    console.log('📊 Call Graph Validation:');
    console.log('  - Has api_name:', !!callGraph.api_name);
    console.log('  - Has service_name:', !!callGraph.service_name);
    console.log('  - Node count:', callGraph.nodes?.length || 0);
    console.log('  - Edge count:', callGraph.edges?.length || 0);

    // Validate metadata
    if (callGraph.metadata) {
        console.log('\n📊 Metadata Validation:');
        console.log('  - Entities:', Object.keys(callGraph.metadata.entities || {}).length);
        console.log('  - Enums:', Object.keys(callGraph.metadata.enums || {}).length);
        console.log('  - Helpers:', Object.keys(callGraph.metadata.helper_methods || {}).length);
        console.log('  - Database:', callGraph.metadata.database?.dialect || 'unknown');
    } else {
        console.error('❌ No metadata found in call graph!');
        throw new Error('Call graph missing metadata');
    }

    // Generate API
    console.log('\n🤖 Generating API configuration...');
    const apiConfig = await generateApiFromMigration(callGraph);

    // Validate output
    console.log('\n📊 Generated API Validation:');
    console.log('  - Has name:', !!apiConfig.name);
    console.log('  - Has nodes:', !!apiConfig.nodes);
    console.log('  - Node count:', Object.keys(apiConfig.nodes || {}).length);
    console.log('  - Has connections:', !!apiConfig.connections);

    return apiConfig;
}

// ============================================================================
// EXAMPLE 5: React Component Usage
// ============================================================================

import { useState } from 'react';

function MigrationComponent() {
    const [loading, setLoading] = useState(false);
    const [apiConfig, setApiConfig] = useState(null);
    const [error, setError] = useState(null);

    const handleMigrate = async (serviceName: string, apiName: string) => {
        setLoading(true);
        setError(null);

        try {
            // 1. Fetch call graph
            const response = await fetch('http://localhost:8000/api/migration/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    service_name: serviceName,
                    api_name: apiName
                })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.statusText}`);
            }

            const callGraph = await response.json();

            // 2. Generate API (simple!)
            const config = await generateApiFromMigration(callGraph);

            setApiConfig(config);

        } catch (err) {
            setError(err.message);
            console.error('Migration failed:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button 
                onClick={() => handleMigrate('ClaimService', 'getClaims')}
                disabled={loading}
            >
                {loading ? 'Migrating...' : 'Migrate API'}
            </button>

            {error && <div className="error">{error}</div>}
            {apiConfig && <pre>{JSON.stringify(apiConfig, null, 2)}</pre>}
        </div>
    );
}

// ============================================================================
// EXAMPLE 6: Testing the Updated Function
// ============================================================================

async function testUpdatedFunction() {
    // Mock call graph with metadata (as returned by backend)
    const mockCallGraph = {
        api_name: 'getClaims',
        service_name: 'ClaimService',
        entry_point: 'com.iris.allofactor.services.impl.ClaimServiceImpl.getClaims',
        nodes: [
            {
                id: 'node1',
                name: 'getClaims',
                class_name: 'ClaimServiceImpl',
                node_type: 'service_impl',
                source_code: 'public GetClaimsOutPut getClaims(...) { ... }',
                dependencies: ['node2']
            }
        ],
        edges: [
            { source: 'node1', target: 'node2', call_type: 'facade' }
        ],
        metadata: {
            entities: {
                MediumClaim: {
                    table_name: 'CLAIM',
                    fields: {
                        C_ID: { column: 'CLINIC_ID', nullable: false },
                        DOS: { column: 'DOS', nullable: true }
                    }
                }
            },
            enums: {
                Claim_ClaimStatus: {
                    CLAIMCREATED: 2,
                    CLAIMFILED: 3
                }
            },
            helper_methods: {},
            conversion_hints: {
                critical_rules: [
                    'ALWAYS use metadata.entities for table/column lookups'
                ]
            },
            database: {
                dialect: 'mysql',
                version: '5.7'
            }
        }
    };

    // Test the function
    console.log('🧪 Testing generateApiFromMigration...\n');

    try {
        const apiConfig = await generateApiFromMigration(mockCallGraph);
        console.log('✅ Success! Generated API config');
        console.log('API name:', apiConfig.name);
        console.log('Node count:', Object.keys(apiConfig.nodes || {}).length);
        return apiConfig;
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        throw error;
    }
}

// ============================================================================
// Run Examples
// ============================================================================

// Uncomment to run:
// basicExample();
// withErrorHandling();
// batchMigration([
//     { service: 'ClaimService', api: 'getClaims' },
//     { service: 'ClaimService', api: 'updateClaim' }
// ]);
// withValidation();
// testUpdatedFunction();

export {
    basicExample,
    withErrorHandling,
    batchMigration,
    withValidation,
    testUpdatedFunction,
    MigrationComponent
};
