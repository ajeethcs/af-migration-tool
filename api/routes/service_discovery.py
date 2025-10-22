"""
Service discovery API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List

from core.service_analyzer import ServiceAnalyzer
from models.schemas import ServiceListResponse, APIListResponse

router = APIRouter()

@router.get("/list", response_model=ServiceListResponse)
async def list_services():
    """
    List all available services in the repository
    """
    try:
        analyzer = ServiceAnalyzer()
        services = analyzer.discover_services()
        
        return ServiceListResponse(
            services=services,
            total_count=len(services)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering services: {str(e)}")

@router.get("/{service_name}/apis", response_model=APIListResponse)
async def list_service_apis(service_name: str):
    """
    List all APIs for a specific service
    """
    try:
        analyzer = ServiceAnalyzer()
        apis = analyzer.get_service_apis(service_name)
        
        if not apis:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found or has no APIs")
        
        return APIListResponse(
            service_name=service_name,
            apis=apis,
            total_count=len(apis)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing APIs: {str(e)}")

@router.get("/{service_name}/apis/{api_name}")
async def get_api_details(service_name: str, api_name: str):
    """
    Get detailed information about a specific API
    """
    try:
        analyzer = ServiceAnalyzer()
        apis = analyzer.get_service_apis(service_name)
        
        for api in apis:
            if api.name == api_name:
                return api
        
        raise HTTPException(status_code=404, detail=f"API '{api_name}' not found in service '{service_name}'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting API details: {str(e)}")
