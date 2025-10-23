# Java to Python Migration Tool

A FastAPI-based tool for migrating Java SOAP services to Python REST APIs. This tool analyzes the existing Java codebase, builds call graphs, and facilitates API-by-API migration.

## Architecture Overview

The tool analyzes two Java repositories:
- **allofactor**: Core business logic, DAOs, and database operations (Hibernate)
- **allofactorservice**: SOAP web services (Controllers and Service implementations)

### Call Flow
```
Controller (SOAP) → Service Interface → ServiceImpl → DaoFacade → DAO → Database
```

## Features

### 1. Service Discovery
- Lists all available services in the repository
- Identifies all APIs within each service
- Extracts method signatures and metadata

### 2. Call Graph Generation
- Traces the complete execution flow of an API
- Identifies all method calls from Controller through DAO implementations
- **Now traces into DAO implementations** (e.g., MediumClaimBODaoImpl)
- Captures all nested method calls within DAOs
- Generates a graph representation with nodes and edges
- Each node represents a method with its source code

### 3. **Schema Metadata Extraction** 🆕
- **Automatically extracts Hibernate entity mappings** from .hbm.xml files
- **Extracts Java enum definitions** with constant values
- **Intelligent metadata filtering** - sends only entities/enums used by the API (97% reduction!)
- Provides complete database schema context for LLM conversion
- Maps Java field names → Database column names
- Maps entity names → Table names
- See [SCHEMA_EXTRACTION.md](SCHEMA_EXTRACTION.md) and [METADATA_FILTERING_GUIDE.md](METADATA_FILTERING_GUIDE.md) for details

### 4. **JSON Optimization** 🆕
- **Automatic 70% size reduction** of call graph JSON before sending to frontend
- Converts large DAO source code to structured `query_logic` representations
- Deduplicates similar helper methods via references
- Compresses logic annotations and groups enums by category
- **Result**: 174 KB → 50 KB typical reduction while preserving all business logic
- Saves both full (debugging) and optimized (frontend) versions
- See [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) and [OPTIMIZATION_QUICK_REF.md](OPTIMIZATION_QUICK_REF.md) for details

### 5. Code Analysis
- Parses Java source files
- Extracts method signatures, parameters, and return types
- Identifies dependencies and method calls
- Analyzes imports and class structure

### 6. Migration Support
- API-by-API migration approach
- Generates JSON representation of call graphs
- Prepares data for UI visualization
- (Future) LLM-based Java to Python code conversion

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
DEFAULT_LLM_MODEL=gpt-4
```

## Usage

### Start the Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation
Interactive API docs: `http://localhost:8000/docs`

## API Endpoints

### Service Discovery

#### List All Services
```
GET /api/services/list
```
Returns all available services with their API counts.

#### List Service APIs
```
GET /api/services/{service_name}/apis
```
Returns all APIs for a specific service.

#### Get API Details
```
GET /api/services/{service_name}/apis/{api_name}
```
Returns detailed information about a specific API.

### Migration

#### Start Migration
```
POST /api/migration/start
Body: {
  "service_name": "ClaimService",
  "api_name": "viewEncounterBO",
  "include_tests": false,
  "llm_model": "gpt-4"
}
```
Starts the migration process and returns a migration ID.

#### Get Migration Status
```
GET /api/migration/status/{migration_id}
```
Returns the current status of a migration job.

#### Get Call Graph
```
GET /api/migration/call-graph/{migration_id}
```
Returns the generated call graph in JSON format.

### Code Analysis

#### Analyze Java File
```
POST /api/analysis/analyze-file
Body: {
  "file_path": "/path/to/file.java"
}
```
Analyzes a Java file and returns its structure.

## Call Graph JSON Format

The call graph is represented as a JSON object with the following structure:

```json
{
  "api_name": "viewEncounterBO",
  "service_name": "ClaimService",
  "entry_point": "node_id_123",
  "nodes": [
    {
      "id": "unique_node_id",
      "name": "methodName",
      "class_name": "com.iris.allofactor.services.impl.ClaimServiceImpl",
      "node_type": "service_impl",
      "signature": {
        "name": "methodName",
        "return_type": "ReturnType",
        "parameters": [
          {
            "name": "param1",
            "type": "String",
            "annotations": []
          }
        ],
        "modifiers": ["public"],
        "annotations": [],
        "throws": []
      },
      "source_code": "// Java source code",
      "converted_code": null,
      "file_path": "/path/to/file.java",
      "line_number": 100,
      "dependencies": ["target_node_id_1", "target_node_id_2"]
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id",
      "call_type": "facade"
    }
  ],
  "metadata": {
    "total_nodes": 10,
    "total_edges": 15
  }
}
```

## Node Types

- **controller**: SOAP endpoint/controller methods
- **service**: Service interface methods
- **service_impl**: Service implementation methods
- **facade**: DaoFacade methods
- **dao**: Data Access Object methods
- **helper**: Helper class methods
- **utility**: Utility class methods

## Project Structure

```
migration-tool/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── api/
│   └── routes/
│       ├── service_discovery.py  # Service discovery endpoints
│       ├── api_migration.py      # Migration endpoints
│       └── code_analysis.py      # Code analysis endpoints
├── core/
│   ├── java_parser.py           # Java source code parser
│   ├── service_analyzer.py      # Service discovery logic
│   └── call_graph_builder.py    # Call graph generation
├── models/
│   └── schemas.py               # Pydantic models
└── output/
    ├── call_graphs/             # Generated call graphs
    └── converted_code/          # Converted Python code
```

## Next Steps

1. **UI Development**: Create a React-based UI to visualize call graphs as node diagrams
2. **LLM Integration**: Implement code conversion using OpenAI/Anthropic APIs
3. **DAO Analysis**: Extend call graph to include DAO method implementations
4. **Test Generation**: Generate Python unit tests for converted code
5. **Database Migration**: Tools for migrating Hibernate entities to SQLAlchemy/Pydantic

## Example Workflow

1. **Discover Services**:
   ```bash
   curl http://localhost:8000/api/services/list
   ```

2. **List APIs for a Service**:
   ```bash
   curl http://localhost:8000/api/services/ClaimService/apis
   ```

3. **Start Migration**:
   ```bash
   curl -X POST http://localhost:8000/api/migration/start \
     -H "Content-Type: application/json" \
     -d '{"service_name": "ClaimService", "api_name": "viewEncounterBO"}'
   ```

4. **Check Status**:
   ```bash
   curl http://localhost:8000/api/migration/status/{migration_id}
   ```

5. **Get Call Graph**:
   ```bash
   curl http://localhost:8000/api/migration/call-graph/{migration_id}
   ```

## Technologies Used

- **FastAPI**: Modern Python web framework
- **javalang**: Java source code parser
- **NetworkX**: Graph analysis (future use)
- **Pydantic**: Data validation
- **OpenAI/Anthropic**: LLM integration (future)

## Contributing

This tool is designed to be extended. Key areas for contribution:
- Enhanced Java parsing for complex patterns
- Better call graph visualization
- LLM prompt engineering for code conversion
- Database schema migration tools
- Test generation
