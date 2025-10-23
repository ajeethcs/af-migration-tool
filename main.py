"""
FastAPI Migration Tool for Java SOAP to Python REST API
This tool analyzes Java SOAP services and generates migration artifacts
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn

from api.routes import service_discovery, api_migration, code_analysis

app = FastAPI(
    title="Java to Python Migration Tool",
    description="Tool for migrating Java SOAP services to Python REST APIs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(service_discovery.router, prefix="/api/services", tags=["Service Discovery"])
app.include_router(api_migration.router, prefix="/api/migration", tags=["API Migration"])
app.include_router(code_analysis.router, prefix="/api/analysis", tags=["Code Analysis"])

@app.get("/")
async def root():
    return {
        "message": "Java to Python Migration Tool API",
        "version": "1.0.0",
        "endpoints": {
            "services": "/api/services",
            "migration": "/api/migration",
            "analysis": "/api/analysis"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
