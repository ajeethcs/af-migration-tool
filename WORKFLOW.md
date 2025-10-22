# Migration Tool Workflow

## Complete Migration Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: DISCOVERY                            │
└─────────────────────────────────────────────────────────────────┘

User Request: "Show me all services"
        ↓
   [FastAPI Endpoint]
   GET /api/services/list
        ↓
   [ServiceAnalyzer]
   - Scans allofactorservice/services/
   - Finds all *Service.java files
   - Matches with *ServiceImpl.java
        ↓
   [JavaParser]
   - Parses each service interface
   - Extracts method signatures
        ↓
   Response: List of services with API counts


┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: API SELECTION                        │
└─────────────────────────────────────────────────────────────────┘

User Request: "Show me APIs in ClaimService"
        ↓
   [FastAPI Endpoint]
   GET /api/services/ClaimService/apis
        ↓
   [ServiceAnalyzer]
   - Loads ClaimService.java
   - Extracts all method declarations
        ↓
   [JavaParser]
   - Parses method signatures
   - Extracts parameters, return types
   - Reads Javadoc comments
        ↓
   Response: List of APIs with full signatures


┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: CALL GRAPH GENERATION                │
└─────────────────────────────────────────────────────────────────┘

User Request: "Migrate ClaimService.viewEncounterBO"
        ↓
   [FastAPI Endpoint]
   POST /api/migration/start
   Body: {service_name, api_name}
        ↓
   [Background Task Started]
   Migration ID: uuid-1234
        ↓
   [CallGraphBuilder]
   
   Step 1: Find Entry Point
   ├─ Load ClaimServiceImpl.java
   ├─ Find viewEncounterBO method
   └─ Create entry node
   
   Step 2: Parse Method Source
   ├─ Extract method body
   ├─ Identify method calls
   └─ Categorize calls:
      ├─ daoFacade.getClaimEncounterBO → FACADE
      ├─ ClaimServiceHelper.populate... → HELPER
      └─ this.someMethod → INTERNAL
   
   Step 3: Resolve Each Call
   For daoFacade.getClaimEncounterBO:
   ├─ Find DaoFacadeImpl.java
   ├─ Locate getClaimEncounterBO method
   ├─ Create facade node
   └─ Create edge: entry → facade
   
   For ClaimServiceHelper.populate...:
   ├─ Find ClaimServiceHelper.java
   ├─ Locate populate method
   ├─ Create helper node
   └─ Create edge: entry → helper
   
   Step 4: Recursive Tracing
   For each new node:
   ├─ Parse its source code
   ├─ Find its method calls
   ├─ Resolve and create nodes
   └─ Continue until depth limit
   
   Step 5: Build Graph Structure
   ├─ Collect all nodes
   ├─ Collect all edges
   ├─ Add metadata
   └─ Export to JSON
        ↓
   [Save to File]
   output/call_graphs/{migration_id}.json
        ↓
   Response: Migration complete with call graph


┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 4: VISUALIZATION (Future)               │
└─────────────────────────────────────────────────────────────────┘

User opens UI → Fetches call graph JSON
        ↓
   [React/Vue Frontend]
   
   For each node in call_graph.nodes:
   ├─ Create visual node
   ├─ Position based on type
   ├─ Color by node_type
   └─ Add click handler
   
   For each edge in call_graph.edges:
   ├─ Draw connection line
   ├─ Style by call_type
   └─ Add arrow direction
        ↓
   [Interactive Diagram]
   ├─ Click node → Show source code
   ├─ Hover edge → Show call type
   ├─ Zoom/Pan → Navigate graph
   └─ Select node → Convert code


┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 5: CODE CONVERSION (Future)             │
└─────────────────────────────────────────────────────────────────┘

User clicks "Convert" on a node
        ↓
   [LLM Integration]
   
   Prepare Context:
   ├─ Node's Java source code
   ├─ Method signature
   ├─ Calling methods (parents)
   ├─ Called methods (children)
   └─ Framework context
   
   Build Prompt:
   ├─ "Convert this Java method to Python"
   ├─ Include Spring → FastAPI mappings
   ├─ Include Hibernate → SQLAlchemy mappings
   ├─ Provide context about dependencies
   └─ Request idiomatic Python code
        ↓
   [OpenAI/Anthropic API]
   ├─ Send prompt
   ├─ Receive Python code
   └─ Parse response
        ↓
   [Validation]
   ├─ Check syntax
   ├─ Verify imports
   └─ Validate structure
        ↓
   [Update Node]
   node.converted_code = python_code
        ↓
   [Display in UI]
   Side-by-side view: Java | Python
```

## Detailed Call Graph Example

### Input API
```java
// ClaimServiceImpl.java
public ViewEncounterBOOutPut viewEncounterBO(
    UserSession userSession, 
    int iClaimID, 
    int iClinicIcdVersion
) {
    ViewEncounterBOOutPut output = null;
    try {
        output = ClaimServiceHelper.populateViewEncounterBOOutPut(
            daoFacade.getClaimEncounterBO(
                iClaimID, 
                iClinicIcdVersion, 
                userSession.getiClinicId()
            )
        );
    } catch(Exception e) {
        // error handling
    }
    return output;
}
```

### Generated Call Graph

```
Node 1: viewEncounterBO (ENTRY POINT)
├─ Type: service_impl
├─ Class: ClaimServiceImpl
├─ Dependencies: [Node 2, Node 3]
└─ Source: [Full Java code above]

Node 2: getClaimEncounterBO (FACADE CALL)
├─ Type: facade
├─ Class: DaoFacadeImpl
├─ Dependencies: [Node 4]
└─ Source: [Facade method code]

Node 3: populateViewEncounterBOOutPut (HELPER CALL)
├─ Type: helper
├─ Class: ClaimServiceHelper
├─ Dependencies: []
└─ Source: [Helper method code]

Node 4: getClaimEncounterBO (DAO CALL)
├─ Type: dao
├─ Class: ClaimEncounterBODao
├─ Dependencies: []
└─ Source: [DAO method with Hibernate query]

Edges:
├─ Node 1 → Node 2 (facade)
├─ Node 1 → Node 3 (helper)
└─ Node 2 → Node 4 (internal)
```

### Visual Representation

```
┌─────────────────────────────────────────┐
│         viewEncounterBO                 │
│      (ClaimServiceImpl)                 │
│         [service_impl]                  │
└───────────┬─────────────────────────────┘
            │
            ├──────────────┬──────────────┐
            │              │              │
            ▼              ▼              │
┌───────────────────┐  ┌──────────────┐  │
│getClaimEncounterBO│  │ populate...  │  │
│  (DaoFacadeImpl)  │  │   (Helper)   │  │
│     [facade]      │  │   [helper]   │  │
└─────────┬─────────┘  └──────────────┘  │
          │                               │
          ▼                               │
┌───────────────────┐                    │
│getClaimEncounterBO│                    │
│ (ClaimEncounter   │                    │
│      BODao)       │                    │
│      [dao]        │                    │
└───────────────────┘                    │
                                         │
         [Hibernate Query]               │
                │                        │
                ▼                        │
         [Database]                      │
                                         │
         [Data Transformation] ◄─────────┘
                │
                ▼
         [Response Object]
```

## API Endpoint Flow

### 1. List Services
```
GET /api/services/list
  ↓
ServiceAnalyzer.discover_services()
  ↓
For each *Service.java:
  ├─ Parse with JavaParser
  ├─ Extract methods
  └─ Create ServiceInfo
  ↓
Return ServiceListResponse
```

### 2. List APIs
```
GET /api/services/{service_name}/apis
  ↓
ServiceAnalyzer.get_service_apis(service_name)
  ↓
Load {service_name}.java
  ↓
JavaParser.get_methods()
  ↓
For each method:
  ├─ Extract signature
  ├─ Extract javadoc
  └─ Create APIInfo
  ↓
Return APIListResponse
```

### 3. Start Migration
```
POST /api/migration/start
Body: {service_name, api_name}
  ↓
Generate migration_id
  ↓
Start background task
  ↓
CallGraphBuilder.build_call_graph()
  ↓
├─ Find entry point
├─ Trace method calls
├─ Build graph structure
└─ Save to JSON
  ↓
Update migration status
  ↓
Return MigrationResponse
```

### 4. Get Call Graph
```
GET /api/migration/call-graph/{migration_id}
  ↓
Load from migration_jobs[migration_id]
  ↓
Return CallGraph JSON
```

## Data Flow

```
Java Source Files
      ↓
[JavaParser]
      ↓
AST (Abstract Syntax Tree)
      ↓
[Method Extraction]
      ↓
Method Info Dict
      ↓
[CallGraphBuilder]
      ↓
Graph Structure (Nodes + Edges)
      ↓
[Pydantic Models]
      ↓
JSON Response
      ↓
[Frontend/UI]
      ↓
Visual Diagram
```

## Error Handling Flow

```
User Request
      ↓
[Try]
  ├─ Parse Java file
  ├─ Extract methods
  └─ Build graph
      ↓
[Catch FileNotFoundError]
  └─ Return 404: Service/API not found
      ↓
[Catch ParseException]
  └─ Return 500: Failed to parse Java file
      ↓
[Catch Exception]
  └─ Return 500: Internal error
      ↓
[Finally]
  └─ Log error details
```

## State Management

```
Migration Job States:

PENDING
  ↓ (start migration)
ANALYZING
  ↓ (building call graph)
CONVERTING (future)
  ↓ (LLM conversion)
COMPLETED
  ↓
[Success]

Or:

ANALYZING
  ↓ (error occurs)
FAILED
  ↓
[Error details in response]
```

## File System Organization

```
migration-tool/
├── Input: Java Source Files
│   ├── allofactor/src/
│   └── allofactorservice/src/
│
├── Processing: Python Modules
│   ├── core/
│   ├── api/
│   └── models/
│
└── Output: Generated Artifacts
    ├── call_graphs/
    │   └── {migration_id}.json
    └── converted_code/
        └── {service_name}/
            └── {api_name}.py
```

## Scalability Considerations

```
Current: Single Request Processing
  User → API → Process → Response

Future: Batch Processing
  User → API → Queue → Worker Pool → Results

Future: Distributed Processing
  User → API → Message Queue → Multiple Workers → Database → Results
```

## Integration Points

```
┌──────────────┐
│   Frontend   │ ← WebSocket for real-time updates
└──────┬───────┘
       │ HTTP/REST
┌──────▼───────┐
│   FastAPI    │
└──────┬───────┘
       │
       ├─→ [Java Repositories] (read-only)
       ├─→ [LLM APIs] (future)
       ├─→ [Database] (future - for persistence)
       └─→ [File System] (JSON output)
```

This workflow provides a complete picture of how the migration tool operates from user request to final output.
