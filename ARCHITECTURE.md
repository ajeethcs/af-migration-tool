# Migration Tool Architecture

## Overview

This document describes the architecture and design decisions for the Java to Python migration tool.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Service    │  │     API      │  │     Code     │      │
│  │  Discovery   │  │  Migration   │  │   Analysis   │      │
│  │   Routes     │  │   Routes     │  │   Routes     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼──────────────────▼──────────────────▼───────┐     │
│  │              Core Processing Layer                  │     │
│  ├─────────────────────────────────────────────────────┤     │
│  │  • ServiceAnalyzer    • CallGraphBuilder           │     │
│  │  • JavaParser         • CodeConverter (future)     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                ┌───────────▼──────────┐
                │   Java Repositories   │
                ├──────────────────────┤
                │  • allofactor        │
                │  • allofactorservice │
                └──────────────────────┘
```

## Component Details

### 1. FastAPI Application Layer

**Purpose**: Provides RESTful API endpoints for the migration tool

**Components**:
- `main.py`: Application entry point, route registration
- `config.py`: Configuration management
- `models/schemas.py`: Pydantic models for request/response validation

### 2. API Routes

#### Service Discovery Routes (`api/routes/service_discovery.py`)
- `GET /api/services/list`: List all services
- `GET /api/services/{service_name}/apis`: List APIs for a service
- `GET /api/services/{service_name}/apis/{api_name}`: Get API details

#### Migration Routes (`api/routes/api_migration.py`)
- `POST /api/migration/start`: Start migration process
- `GET /api/migration/status/{migration_id}`: Check migration status
- `GET /api/migration/call-graph/{migration_id}`: Retrieve call graph

#### Code Analysis Routes (`api/routes/code_analysis.py`)
- `POST /api/analysis/convert`: Convert Java code to Python (future)
- `POST /api/analysis/analyze-file`: Analyze Java file structure

### 3. Core Processing Layer

#### JavaParser (`core/java_parser.py`)

**Purpose**: Parse Java source files and extract structural information

**Key Methods**:
- `get_methods()`: Extract all methods with signatures
- `get_imports()`: Get import statements
- `get_fields()`: Get class fields
- `find_method_calls()`: Identify method invocations
- `_extract_method_source()`: Extract method source code

**Technology**: Uses `javalang` library for AST parsing

#### ServiceAnalyzer (`core/service_analyzer.py`)

**Purpose**: Discover and analyze services and their APIs

**Key Methods**:
- `discover_services()`: Find all service interfaces
- `get_service_apis()`: List APIs for a service
- `find_method_in_implementation()`: Locate method in ServiceImpl

**Process**:
1. Scans `allofactorservice/src/com/iris/allofactor/services/` for service interfaces
2. Matches with implementation files in `services/impl/`
3. Extracts method signatures and metadata

#### CallGraphBuilder (`core/call_graph_builder.py`)

**Purpose**: Build complete call graphs for API methods

**Key Methods**:
- `build_call_graph()`: Main entry point for graph construction
- `_trace_method_calls()`: Recursively trace method invocations
- `_extract_method_calls()`: Parse source code for method calls
- `_resolve_method_call()`: Find method definitions

**Algorithm**:
```
1. Start with API method in ServiceImpl
2. Parse method source code
3. Identify method calls:
   - daoFacade.method() → Facade calls
   - HelperClass.method() → Helper calls
   - this.method() → Internal calls
4. For each call:
   a. Locate method definition
   b. Create node in graph
   c. Create edge from caller to callee
   d. Recursively process callee (depth-limited)
5. Return complete graph
```

**Call Pattern Recognition**:
- **Facade calls**: `daoFacade\.(\w+)\s*\(`
- **Helper calls**: `(\w+Helper)\.(\w+)\s*\(`
- **Internal calls**: `this\.(\w+)\s*\(`

### 4. Data Models

#### Node Types
```python
class NodeType(Enum):
    CONTROLLER = "controller"      # SOAP endpoints
    SERVICE = "service"            # Service interfaces
    SERVICE_IMPL = "service_impl"  # Service implementations
    FACADE = "facade"              # DaoFacade methods
    DAO = "dao"                    # DAO methods
    HELPER = "helper"              # Helper classes
    UTILITY = "utility"            # Utility classes
```

#### Call Graph Structure
```python
CallGraph:
  - api_name: str
  - service_name: str
  - entry_point: str (node ID)
  - nodes: List[MethodNode]
  - edges: List[CallEdge]
  - metadata: Dict

MethodNode:
  - id: str (unique identifier)
  - name: str
  - class_name: str (fully qualified)
  - node_type: NodeType
  - signature: MethodSignature
  - source_code: str (Java code)
  - converted_code: str (Python code, future)
  - file_path: str
  - line_number: int
  - dependencies: List[str] (target node IDs)

CallEdge:
  - source: str (node ID)
  - target: str (node ID)
  - call_type: str (facade, helper, internal)
```

## Java Application Architecture

### Layer Structure

```
┌─────────────────────────────────────────┐
│         SOAP Web Service Layer          │
│      (allofactorservice repository)     │
├─────────────────────────────────────────┤
│  • Service Interfaces (ClaimService)    │
│  • Service Implementations              │
│    (ClaimServiceImpl)                   │
└──────────────────┬──────────────────────┘
                   │ calls
┌──────────────────▼──────────────────────┐
│         Business Logic Layer            │
│        (allofactor repository)          │
├─────────────────────────────────────────┤
│  • DaoFacade (central access point)     │
│  • Business Logic                       │
│  • DAOs (Data Access Objects)           │
│  • Hibernate Entities                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│            Database Layer               │
│         (Hibernate/JDBC)                │
└─────────────────────────────────────────┘
```

### Call Flow Example

```
1. SOAP Request
   ↓
2. ClaimService.viewEncounterBO(userSession, claimId, version)
   ↓
3. ClaimServiceImpl.viewEncounterBO(...)
   ↓
4. daoFacade.getClaimEncounterBO(claimId, version, clinicId)
   ↓
5. DaoFacadeImpl.getClaimEncounterBO(...)
   ↓
6. ClaimEncounterBODao.getClaimEncounterBO(...)
   ↓
7. Hibernate Query
   ↓
8. Database
```

## Migration Process

### Phase 1: Discovery (Current)
1. User selects a service
2. System lists all APIs in that service
3. User selects an API to migrate

### Phase 2: Analysis (Current)
1. System builds call graph starting from API method
2. Traces through ServiceImpl → Facade → DAO
3. Extracts source code for each method
4. Generates JSON representation

### Phase 3: Visualization (Future - UI)
1. Display call graph as interactive node diagram
2. Each node shows method signature and code
3. Edges show call relationships
4. Allow navigation through the graph

### Phase 4: Conversion (Future - LLM)
1. For each node, convert Java code to Python
2. Use LLM with context about:
   - Method signature
   - Dependencies
   - Framework patterns (Spring → FastAPI, Hibernate → SQLAlchemy)
3. Generate Python equivalent
4. Store in node.converted_code

### Phase 5: Generation (Future)
1. Generate complete Python module structure
2. Create FastAPI endpoints
3. Generate SQLAlchemy models
4. Create unit tests
5. Generate documentation

## Design Decisions

### 1. Why FastAPI?
- Modern Python web framework
- Automatic API documentation (Swagger/OpenAPI)
- Type hints and validation with Pydantic
- Async support for future scalability
- Easy integration with LLMs

### 2. Why javalang?
- Pure Python Java parser
- No JVM dependency
- AST-based parsing for accurate analysis
- Handles Java 8 syntax

### 3. Graph Representation
- Nodes represent methods (not classes) for granular analysis
- Edges represent direct method calls
- Supports multiple call types (facade, helper, internal)
- JSON format for easy serialization and UI integration

### 4. API-by-API Migration
- Reduces complexity
- Allows incremental migration
- Easier testing and validation
- Can run old and new systems in parallel

### 5. Depth Limiting
- Prevents infinite recursion
- Limits graph size for performance
- Focuses on direct dependencies
- Can be adjusted based on needs

## Future Enhancements

### 1. Enhanced Parsing
- Support for more call patterns
- Lambda expressions
- Anonymous classes
- Reflection calls

### 2. DAO Analysis
- Extract SQL queries from Hibernate
- Generate SQLAlchemy models
- Map entity relationships

### 3. Test Generation
- Generate Python unit tests
- Mock external dependencies
- Test data generation

### 4. UI Development
- React-based visualization
- Interactive node editing
- Code comparison view
- Migration progress tracking

### 5. LLM Integration
- OpenAI GPT-4 for code conversion
- Anthropic Claude for analysis
- Custom prompts for different patterns
- Context-aware conversion

### 6. Batch Processing
- Migrate multiple APIs simultaneously
- Dependency resolution
- Conflict detection

### 7. Database Migration
- Schema extraction
- Migration scripts
- Data transformation

## Performance Considerations

### Current Limitations
- Single-threaded processing
- In-memory graph storage
- No caching of parsed files
- Limited to ~100 nodes per graph

### Optimization Opportunities
- Cache parsed Java files
- Parallel file parsing
- Database for large graphs
- Incremental graph updates
- Lazy loading of source code

## Security Considerations

### Current
- No authentication (local use)
- File system access restricted to configured paths
- No code execution

### Future
- API authentication
- Rate limiting for LLM calls
- Code sanitization
- Audit logging

## Testing Strategy

### Unit Tests
- JavaParser functionality
- ServiceAnalyzer discovery
- CallGraphBuilder graph construction
- API endpoint responses

### Integration Tests
- End-to-end migration flow
- Multiple service types
- Complex call patterns

### Test Script
- `test_migration_tool.py` provides basic validation
- Tests service discovery, API listing, and call graph generation
