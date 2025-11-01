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


def prune_call_graph_for_llm(call_graph: dict) -> dict:
    """
    Aggressively prune call graph for LLM to reduce token count.
    
    This removes all non-essential fields while preserving 100% of business logic
    and database schema information needed for HQL-to-SQL conversion.
    
    REMOVED (useless for LLM):
    - Node: id, class_name, annotations everywhere
    - Signature: Keep only name, return_type, parameters (with name & type only)
    - Dependencies: KEPT (needed for execution order)
    - Helper methods: Optimized signature
    - DTOs: Optimized structure
    - logic_annotations, converted_code, file_path, line_number
    - migration_id, status, message, errors, edges
    - metadata.conversion_hints
    
    PRESERVED (critical for LLM):
    - source_code: Complete business logic
    - signature.name, return_type, parameters (name & type only)
    - name, node_type: Node identification
    - dependencies: Call flow and execution order
    - metadata.database: Database dialect info
    - metadata.entities: Table name + fields with column names and types
    - metadata.enums: Enum values
    - metadata.helper_methods: Optimized with source code
    - metadata.dtos: Field names only
    """
    import copy
    pruned = copy.deepcopy(call_graph)
    
    # Remove top-level useless fields
    pruned.pop('migration_id', None)
    pruned.pop('status', None)
    pruned.pop('message', None)
    pruned.pop('errors', None)
    pruned.pop('edges', None)  # Redundant - already in dependencies
    
    # Prune each node
    if 'nodes' in pruned and isinstance(pruned['nodes'], list):
        for node in pruned['nodes']:
            # Remove useless fields
            node.pop('id', None)  # Not needed, name is enough
            node.pop('class_name', None)  # Not needed for Python
            node.pop('logic_annotations', None)
            node.pop('converted_code', None)
            node.pop('file_path', None)
            node.pop('line_number', None)
            
            # Optimize signature - keep only essentials
            if 'signature' in node and isinstance(node['signature'], dict):
                sig = node['signature']
                optimized_sig = {
                    'name': sig.get('name'),
                    'return_type': sig.get('return_type')
                }
                
                # Optimize parameters - keep only name and type
                if 'parameters' in sig and isinstance(sig['parameters'], list):
                    optimized_sig['parameters'] = [
                        {'name': p.get('name'), 'type': p.get('type')}
                        for p in sig['parameters']
                    ]
                
                node['signature'] = optimized_sig
            
            # Keep dependencies - needed for execution order
    
    # Optimize metadata
    if 'metadata' in pruned and isinstance(pruned['metadata'], dict):
        pruned['metadata'].pop('conversion_hints', None)
        # Keep database dialect info - needed for SQL generation
        
        # Optimize entities - keep table name, fields with column names and types
        if 'entities' in pruned['metadata']:
            optimized_entities = {}
            for entity_name, entity_data in pruned['metadata']['entities'].items():
                if isinstance(entity_data, dict):
                    optimized_entities[entity_name] = {
                        'table_name': entity_data.get('table_name', entity_name.lower()),
                        'fields': {}
                    }
                    
                    # Keep field name, column name, and type for each field
                    if 'fields' in entity_data and isinstance(entity_data['fields'], dict):
                        for field_name, field_data in entity_data['fields'].items():
                            if isinstance(field_data, dict):
                                optimized_entities[entity_name]['fields'][field_name] = {
                                    'column': field_data.get('column', field_name.lower()),
                                    'type': field_data.get('type', 'VARCHAR'),
                                    'nullable': field_data.get('nullable', True)
                                }
            pruned['metadata']['entities'] = optimized_entities
        
        # Optimize helper methods - keep only essentials
        if 'helper_methods' in pruned['metadata']:
            for method_name, method_data in pruned['metadata']['helper_methods'].items():
                if isinstance(method_data, dict):
                    # Remove unnecessary fields
                    method_data.pop('class_name', None)
                    method_data.pop('file_path', None)
                    method_data.pop('line_number', None)
                    
                    # Optimize signature
                    if 'signature' in method_data and isinstance(method_data['signature'], dict):
                        sig = method_data['signature']
                        optimized_sig = {
                            'name': sig.get('name'),
                            'return_type': sig.get('return_type')
                        }
                        
                        if 'parameters' in sig and isinstance(sig['parameters'], list):
                            optimized_sig['parameters'] = [
                                {'name': p.get('name'), 'type': p.get('type')}
                                for p in sig['parameters']
                            ]
                        
                        method_data['signature'] = optimized_sig
                    
                    # Keep: source_code (critical for business logic)
        
        # Optimize DTOs - keep only essential structure
        if 'dtos' in pruned['metadata']:
            for dto_name, dto_data in pruned['metadata']['dtos'].items():
                if isinstance(dto_data, dict):
                    # Remove unnecessary fields
                    dto_data.pop('package', None)
                    dto_data.pop('fully_qualified_name', None)
                    dto_data.pop('extends', None)
                    dto_data.pop('implements', None)
                    dto_data.pop('modifiers', None)
                    dto_data.pop('annotations', None)
                    
                    # Optimize fields - keep only field names as array
                    if 'fields' in dto_data:
                        pruned['metadata']['dtos'][dto_name] = {
                            'fields': list(dto_data['fields'].keys())
                        }
    
    return pruned


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
async def get_call_graph(migration_id: str, pruned: bool = False):
    """
    Get the call graph for a migration job
    
    Args:
        migration_id: The migration job ID
        pruned: If True, return pruned version optimized for LLM (removes useless fields)
    """
    if migration_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")

    job = migration_jobs[migration_id]

    if not job.call_graph:
        raise HTTPException(
            status_code=404, detail="Call graph not yet generated")

    if pruned:
        return prune_call_graph_for_llm(job.call_graph)
    
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
                call_graph.model_dump(mode='json'),
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


@router.delete("/cache")
async def clear_cache():
    """
    Clear the call graph cache
    
    Use this endpoint to force regeneration of call graphs with latest features
    """
    cache_size = len(call_graph_cache)
    call_graph_cache.clear()
    return {
        "message": f"Cache cleared successfully. Removed {cache_size} cached call graphs.",
        "cleared_count": cache_size
    }


@router.get("/cache/status")
async def get_cache_status():
    """
    Get information about the current cache
    """
    cached_apis = [
        {"service": service, "api": api}
        for service, api in call_graph_cache.keys()
    ]
    return {
        "cached_count": len(call_graph_cache),
        "cached_apis": cached_apis
    }
