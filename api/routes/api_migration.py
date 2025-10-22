"""
API migration endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
import json

from core.call_graph_builder import CallGraphBuilder
from core.business_logic_enhancer import BusinessLogicEnhancer
from models.schemas import (
    MigrationRequest, MigrationResponse, MigrationStatus
)
from config import CALL_GRAPHS_DIR

router = APIRouter()

# In-memory storage for migration status (in production, use a database)
migration_jobs: Dict[str, MigrationResponse] = {}

@router.post("/start", response_model=MigrationResponse)
async def start_migration(request: MigrationRequest, background_tasks: BackgroundTasks):
    """
    Start the migration process for a specific API
    """
    try:
        # Generate migration ID
        migration_id = str(uuid.uuid4())
        
        # Create initial response
        response = MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.ANALYZING,
            message="Migration started. Building call graph..."
        )
        
        migration_jobs[migration_id] = response
        
        # Start migration in background
        background_tasks.add_task(
            perform_migration,
            migration_id,
            request.service_name,
            request.api_name,
            request.llm_model
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting migration: {str(e)}")

@router.get("/status/{migration_id}", response_model=MigrationResponse)
async def get_migration_status(migration_id: str):
    """
    Get the status of a migration job
    """
    if migration_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    return migration_jobs[migration_id]

@router.get("/call-graph/{migration_id}")
async def get_call_graph(migration_id: str):
    """
    Get the call graph for a migration job
    """
    if migration_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    job = migration_jobs[migration_id]
    
    if not job.call_graph:
        raise HTTPException(status_code=404, detail="Call graph not yet generated")
    
    return job.call_graph

async def perform_migration(
    migration_id: str,
    service_name: str,
    api_name: str,
    llm_model: str
):
    """
    Perform the actual migration (background task)
    """
    try:
        # Update status
        migration_jobs[migration_id].status = MigrationStatus.ANALYZING
        migration_jobs[migration_id].message = "Building call graph..."
        
        # Build call graph with schema metadata
        builder = CallGraphBuilder()
        call_graph = builder.build_call_graph(
            service_name=service_name,
            api_name=api_name,
            include_schema=True  # Include Hibernate mappings and enums
        )
        
        # Enhance with business logic and filter metadata
        migration_jobs[migration_id].message = "Enhancing with business logic and filtering metadata..."
        enhancer = BusinessLogicEnhancer()
        enhanced_graph = enhancer.enhance_call_graph(
            call_graph.model_dump(),
            include_all=True,
            filter_metadata=True  # ✅ Filter to only relevant entities/enums
        )
        
        # Save enhanced call graph to file
        output_file = CALL_GRAPHS_DIR / f"{migration_id}.json"
        with open(output_file, 'w') as f:
            json.dump(enhanced_graph, f, indent=2)
        
        # Update response with enhanced call graph
        migration_jobs[migration_id].call_graph = enhanced_graph
        migration_jobs[migration_id].status = MigrationStatus.COMPLETED
        
        # Get metadata stats for message
        metadata = enhanced_graph.get('metadata', {})
        entity_count = len(metadata.get('entities', {}))
        enum_count = len(metadata.get('enums', {}))
        helper_count = len(metadata.get('helper_methods', {}))
        
        migration_jobs[migration_id].message = (
            f"Call graph generated with {len(enhanced_graph.get('nodes', []))} nodes. "
            f"Metadata: {entity_count} entities, {enum_count} enums, {helper_count} helpers"
        )
        
    except FileNotFoundError as e:
        migration_jobs[migration_id].status = MigrationStatus.FAILED
        migration_jobs[migration_id].message = str(e)
        migration_jobs[migration_id].errors.append(str(e))
    except Exception as e:
        migration_jobs[migration_id].status = MigrationStatus.FAILED
        migration_jobs[migration_id].message = f"Migration failed: {str(e)}"
        migration_jobs[migration_id].errors.append(str(e))
