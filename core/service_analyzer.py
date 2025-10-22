"""
Service discovery and analysis module
"""
from pathlib import Path
from typing import List, Dict, Optional
import re

from config import SERVICES_PATH, SERVICES_IMPL_PATH
from core.java_parser import JavaParser
from models.schemas import ServiceInfo, APIInfo, MethodSignature, MethodParameter

class ServiceAnalyzer:
    """Analyzes Java services and discovers APIs"""
    
    def __init__(self):
        self.services_path = SERVICES_PATH
        self.services_impl_path = SERVICES_IMPL_PATH
    
    def discover_services(self) -> List[ServiceInfo]:
        """Discover all services in the repository"""
        services = []
        
        # Find all service interface files
        if not self.services_path.exists():
            return services
        
        for service_file in self.services_path.glob("*.java"):
            if service_file.name.endswith("Service.java") and not service_file.name.startswith("impl"):
                service_info = self._analyze_service(service_file)
                if service_info:
                    services.append(service_info)
        
        return services
    
    def _analyze_service(self, service_file: Path) -> Optional[ServiceInfo]:
        """Analyze a single service file"""
        try:
            parser = JavaParser(service_file)
            
            # Get service name
            service_name = service_file.stem
            
            # Find implementation file
            impl_file = self.services_impl_path / f"{service_name}Impl.java"
            
            # Get all methods (APIs)
            methods = parser.get_methods()
            api_names = [method["name"] for method in methods]
            
            return ServiceInfo(
                name=service_name,
                interface_path=str(service_file),
                implementation_path=str(impl_file) if impl_file.exists() else "",
                api_count=len(api_names),
                apis=api_names
            )
        except Exception as e:
            print(f"Error analyzing service {service_file}: {e}")
            return None
    
    def get_service_apis(self, service_name: str) -> List[APIInfo]:
        """Get all APIs for a specific service"""
        service_file = self.services_path / f"{service_name}.java"
        
        if not service_file.exists():
            return []
        
        parser = JavaParser(service_file)
        methods = parser.get_methods()
        
        apis = []
        for method in methods:
            # Create method signature
            parameters = [
                MethodParameter(
                    name=p["name"],
                    type=p["type"],
                    annotations=p.get("annotations", [])
                )
                for p in method["parameters"]
            ]
            
            signature = MethodSignature(
                name=method["name"],
                return_type=method["return_type"],
                parameters=parameters,
                modifiers=method.get("modifiers", []),
                annotations=method.get("annotations", []),
                throws=method.get("throws", [])
            )
            
            # Extract description from javadoc if available
            description = self._extract_javadoc(method.get("source_code", ""))
            
            apis.append(APIInfo(
                name=method["name"],
                signature=signature,
                service_name=service_name,
                description=description
            ))
        
        return apis
    
    def _extract_javadoc(self, source_code: str) -> Optional[str]:
        """Extract javadoc comment from method source"""
        if not source_code:
            return None
        
        # Look for javadoc comment
        javadoc_pattern = r'/\*\*(.*?)\*/'
        match = re.search(javadoc_pattern, source_code, re.DOTALL)
        
        if match:
            javadoc = match.group(1)
            # Clean up the javadoc
            lines = javadoc.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('*'):
                    line = line[1:].strip()
                if line and not line.startswith('@'):
                    cleaned_lines.append(line)
            
            return ' '.join(cleaned_lines)
        
        return None
    
    def get_service_implementation(self, service_name: str) -> Optional[JavaParser]:
        """Get the parser for service implementation"""
        impl_file = self.services_impl_path / f"{service_name}Impl.java"
        
        if not impl_file.exists():
            return None
        
        return JavaParser(impl_file)
    
    def find_method_in_implementation(self, service_name: str, method_name: str) -> Optional[Dict]:
        """Find a specific method in the service implementation"""
        parser = self.get_service_implementation(service_name)
        
        if not parser:
            return None
        
        methods = parser.get_methods()
        for method in methods:
            if method["name"] == method_name:
                return method
        
        return None
