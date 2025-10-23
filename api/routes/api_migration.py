"""
API migration endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
import json

from core.call_graph_builder import CallGraphBuilder
from core.business_logic_enhancer import BusinessLogicEnhancer
from core.call_graph_optimizer import CallGraphOptimizer
from models.schemas import (
    MigrationRequest, MigrationResponse, MigrationStatus
)
from config import CALL_GRAPHS_DIR

router = APIRouter()

# In-memory storage for migration status (in production, use a database)
migration_jobs: Dict[str, MigrationResponse] = {}

# In-memory cache for call graphs: {(service_name, api_name): call_graph}
call_graph_cache: Dict[tuple, dict] = {}


@router.post("/start", response_model=MigrationResponse)
async def start_migration(request: MigrationRequest, background_tasks: BackgroundTasks):
    """
    Start the migration process for a specific API
    """
    try:
        migration_id = str(uuid.uuid4())
        response = MigrationResponse(
            migration_id=migration_id,
            status=MigrationStatus.ANALYZING,
            message="Migration started. Building call graph..."
        )
        migration_jobs[migration_id] = response

        # Check cache before starting migration
        cache_key = (request.service_name, request.api_name)
        if cache_key in call_graph_cache:
            # Use cached call graph, skip background task
            cached_graph = call_graph_cache[cache_key]
            migration_jobs[migration_id].call_graph = cached_graph
            migration_jobs[migration_id].status = MigrationStatus.COMPLETED
            metadata = cached_graph.get('metadata', {})
            entity_count = len(metadata.get('entities', {}))
            enum_count = len(metadata.get('enums', {}))
            helper_count = len(metadata.get('helper_methods', {}))
            migration_jobs[migration_id].message = (
                f"Call graph (cached) with {len(cached_graph.get('nodes', []))} nodes. "
                f"Metadata: {entity_count} entities, {enum_count} enums, {helper_count} helpers."
            )
        else:
            # Not cached, perform migration in background
            background_tasks.add_task(
                perform_migration,
                migration_id,
                request.service_name,
                request.api_name,
                request.llm_model
            )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting migration: {str(e)}")


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
        raise HTTPException(
            status_code=404, detail="Call graph not yet generated")

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
        migration_jobs[migration_id].status = MigrationStatus.ANALYZING
        migration_jobs[migration_id].message = "Building call graph..."

        cache_key = (service_name, api_name)
        if cache_key in call_graph_cache:
            # Use cached call graph
            optimized_graph = call_graph_cache[cache_key]
        else:
            builder = CallGraphBuilder()
            call_graph = builder.build_call_graph(
                service_name=service_name,
                api_name=api_name,
                include_schema=True
            )
            migration_jobs[migration_id].message = "Enhancing with business logic and filtering metadata..."
            enhancer = BusinessLogicEnhancer()
            enhanced_graph = enhancer.enhance_call_graph(
                call_graph.model_dump(),
                include_all=True,
                filter_metadata=True
            )
            optimized_graph = enhanced_graph
            # Cache the optimized graph
            call_graph_cache[cache_key] = optimized_graph

            # Save both versions to file
            full_output_file = CALL_GRAPHS_DIR / f"{migration_id}_full.json"
            optimized_output_file = CALL_GRAPHS_DIR / f"{migration_id}.json"
            with open(full_output_file, 'w') as f:
                json.dump(enhanced_graph, f, indent=2)
            with open(optimized_output_file, 'w') as f:
                json.dump(optimized_graph, f, indent=2)

        migration_jobs[migration_id].call_graph = optimized_graph
        migration_jobs[migration_id].status = MigrationStatus.COMPLETED

        metadata = optimized_graph.get('metadata', {})
        entity_count = len(metadata.get('entities', {}))
        enum_count = len(metadata.get('enums', {}))
        helper_count = len(metadata.get('helper_methods', {}))
        migration_jobs[migration_id].message = (
            f"Call graph generated with {len(optimized_graph.get('nodes', []))} nodes. "
            f"Metadata: {entity_count} entities, {enum_count} enums, {helper_count} helpers. "
        )

    except FileNotFoundError as e:
        migration_jobs[migration_id].status = MigrationStatus.FAILED
        migration_jobs[migration_id].message = str(e)
        migration_jobs[migration_id].errors.append(str(e))
    except Exception as e:
        migration_jobs[migration_id].status = MigrationStatus.FAILED
        migration_jobs[migration_id].message = f"Migration failed: {str(e)}"
        migration_jobs[migration_id].errors.append(str(e))
