# Quick Start Guide

## Installation & Setup

### 1. Install Python Dependencies

```bash
cd "c:\Users\pc\Desktop\trillium\af claims\migration-tool"
pip install -r requirements.txt
```

### 2. Verify Installation

Run the test script to verify everything is working:

```bash
python test_migration_tool.py
```

This will:
- Discover all services in the repository
- List APIs for ClaimService
- Generate a sample call graph

### 3. Start the FastAPI Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

### 4. Access API Documentation

Open your browser and go to:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Basic Usage

### Step 1: Discover Available Services

**Request:**
```bash
curl http://localhost:8000/api/services/list
```

**Response:**
```json
{
  "services": [
    {
      "name": "ClaimService",
      "interface_path": "...",
      "implementation_path": "...",
      "api_count": 150,
      "apis": ["viewEncounterBO", "addorEditClaim", ...]
    },
    ...
  ],
  "total_count": 18
}
```

### Step 2: List APIs for a Service

**Request:**
```bash
curl http://localhost:8000/api/services/ClaimService/apis
```

**Response:**
```json
{
  "service_name": "ClaimService",
  "apis": [
    {
      "name": "viewEncounterBO",
      "signature": {
        "name": "viewEncounterBO",
        "return_type": "ViewEncounterBOOutPut",
        "parameters": [
          {
            "name": "userSession",
            "type": "UserSession",
            "annotations": []
          },
          {
            "name": "iClaimID",
            "type": "int",
            "annotations": []
          }
        ]
      },
      "service_name": "ClaimService",
      "description": "View encounter business object"
    }
  ],
  "total_count": 150
}
```

### Step 3: Start Migration for an API

**Request:**
```bash
curl -X POST http://localhost:8000/api/migration/start \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "ClaimService",
    "api_name": "viewEncounterBO",
    "include_tests": false,
    "llm_model": "gpt-4"
  }'
```

**Response:**
```json
{
  "migration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analyzing",
  "message": "Migration started. Building call graph...",
  "errors": []
}
```

### Step 4: Check Migration Status

**Request:**
```bash
curl http://localhost:8000/api/migration/status/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "migration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Call graph generated successfully with 15 nodes",
  "errors": []
}
```

### Step 5: Get the Call Graph

**Request:**
```bash
curl http://localhost:8000/api/migration/call-graph/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "api_name": "viewEncounterBO",
  "service_name": "ClaimService",
  "entry_point": "com.iris.allofactor.services.impl.ClaimServiceImpl.viewEncounterBO_abc123",
  "nodes": [
    {
      "id": "com.iris.allofactor.services.impl.ClaimServiceImpl.viewEncounterBO_abc123",
      "name": "viewEncounterBO",
      "class_name": "com.iris.allofactor.services.impl.ClaimServiceImpl",
      "node_type": "service_impl",
      "signature": {
        "name": "viewEncounterBO",
        "return_type": "ViewEncounterBOOutPut",
        "parameters": [...]
      },
      "source_code": "public ViewEncounterBOOutPut viewEncounterBO(...) { ... }",
      "file_path": "...",
      "line_number": 443,
      "dependencies": ["facade_node_id_1", "helper_node_id_2"]
    },
    ...
  ],
  "edges": [
    {
      "source": "service_impl_node_id",
      "target": "facade_node_id",
      "call_type": "facade"
    },
    ...
  ],
  "metadata": {
    "total_nodes": 15,
    "total_edges": 20
  }
}
```

## Understanding the Call Graph

### Node Types
- **service_impl**: Entry point - the API method in ServiceImpl
- **facade**: Methods in DaoFacade
- **dao**: Data Access Object methods
- **helper**: Helper class methods
- **utility**: Utility methods

### Call Graph Structure
Each node represents a method in the call chain:
1. **Entry Point**: The API method you selected
2. **Dependencies**: Methods called by this method
3. **Source Code**: The actual Java code
4. **Edges**: Show the call relationships

### Example Flow
```
viewEncounterBO (service_impl)
  ↓
  ├─→ ClaimServiceHelper.populateViewEncounterBOOutPut (helper)
  │
  └─→ daoFacade.getClaimEncounterBO (facade)
       ↓
       └─→ ClaimEncounterBODao.getClaimEncounterBO (dao)
```

## Next Steps

### For UI Development
The call graph JSON is ready to be consumed by a React/Vue frontend:
- Each node can be rendered as a visual node
- Edges can be rendered as connections
- Click on nodes to view source code
- Highlight the execution path

### For Code Conversion
The call graph provides all the information needed for LLM-based conversion:
- Method signatures
- Source code
- Dependencies
- Call context

### Example UI Integration
```javascript
// Fetch call graph
const response = await fetch(
  `http://localhost:8000/api/migration/call-graph/${migrationId}`
);
const callGraph = await response.json();

// Render nodes
callGraph.nodes.forEach(node => {
  renderNode({
    id: node.id,
    label: node.name,
    type: node.node_type,
    code: node.source_code
  });
});

// Render edges
callGraph.edges.forEach(edge => {
  renderEdge({
    from: edge.source,
    to: edge.target,
    type: edge.call_type
  });
});
```

## Common Services to Migrate

Based on the repository structure, here are the main services:

1. **ClaimService** - Claims management (150+ APIs)
2. **EmrService** - Electronic Medical Records
3. **CalendarService** - Appointment scheduling
4. **AccountsService** - Patient accounts
5. **AdministrationService** - System administration
6. **ArService** - Accounts Receivable
7. **AutoSyncService** - Data synchronization
8. **DocumentService** - Document management
9. **FaxService** - Fax integration
10. **TaskService** - Task management

## Troubleshooting

### Issue: "Service not found"
- Verify the service name matches exactly (case-sensitive)
- Check that the service file exists in `allofactorservice/src/com/iris/allofactor/services/`

### Issue: "API not found"
- Verify the API name matches the method name in the service interface
- Check for typos in the method name

### Issue: "Call graph generation failed"
- The API might use patterns not yet supported
- Check the error message for details
- Some complex APIs might exceed the depth limit

### Issue: "No services discovered"
- Verify the repository paths in `config.py`
- Ensure the Java source files are accessible
- Check file permissions

## Configuration

Edit `config.py` to adjust:
- Repository paths
- Output directories
- Depth limits for call graph generation
- LLM settings (for future use)

## Output Files

Generated files are saved in:
- **Call Graphs**: `output/call_graphs/{migration_id}.json`
- **Converted Code**: `output/converted_code/` (future)

## Performance Tips

- Start with smaller APIs to test the system
- Use the depth limit to control graph size
- Cache frequently accessed services
- Run tests before starting large migrations

## Support

For issues or questions:
1. Check the ARCHITECTURE.md for detailed design information
2. Review the test script output for diagnostics
3. Examine the generated call graph JSON for insights
