"""
Debug script to investigate why DAO calls aren't being detected
"""
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

from core.java_parser import JavaParser
from config import FACADE_PATH, SERVICES_IMPL_PATH

def debug_facade_method():
    """Debug the facade method extraction"""
    print("\n" + "="*60)
    print("DEBUG: Facade Method Extraction")
    print("="*60)
    
    facade_file = FACADE_PATH / "DaoFacadeImpl.java"
    print(f"\nParsing: {facade_file}")
    
    parser = JavaParser(facade_file)
    methods = parser.get_methods()
    
    # Find getMediumClaimBO method
    target_method = None
    for method in methods:
        if method["name"] == "getMediumClaimBO":
            target_method = method
            break
    
    if target_method:
        print(f"\n✓ Found method: {target_method['name']}")
        print(f"  Return type: {target_method['return_type']}")
        print(f"  Line number: {target_method['line_number']}")
        print(f"\n  Source code:")
        print("  " + "-"*56)
        source = target_method.get('source_code', '')
        if source:
            for line in source.split('\n')[:20]:  # Show first 20 lines
                print(f"  {line}")
        else:
            print("  [NO SOURCE CODE EXTRACTED]")
        print("  " + "-"*56)
        
        # Test pattern matching on this source
        print("\n  Testing DAO pattern matching:")
        
        # Pattern for DAO field calls
        dao_field_pattern = r'this\.(\w+Dao)\.(\w+)\s*\('
        matches = list(re.finditer(dao_field_pattern, source))
        
        if matches:
            print(f"  ✓ Found {len(matches)} DAO field call(s):")
            for match in matches:
                print(f"    - this.{match.group(1)}.{match.group(2)}()")
        else:
            print("  ✗ No DAO field calls found")
            
            # Try to understand why
            print("\n  Checking for 'mediumClaimBODao' in source:")
            if 'mediumClaimBODao' in source:
                print("  ✓ String 'mediumClaimBODao' found in source")
                # Show the context
                for i, line in enumerate(source.split('\n')):
                    if 'mediumClaimBODao' in line:
                        print(f"    Line {i}: {line.strip()}")
            else:
                print("  ✗ String 'mediumClaimBODao' NOT found in source")
    else:
        print("\n✗ Method 'getMediumClaimBO' not found")
        print(f"\nAvailable methods ({len(methods)}):")
        for method in methods[:10]:
            print(f"  - {method['name']}")

def debug_service_impl():
    """Debug the service implementation method"""
    print("\n" + "="*60)
    print("DEBUG: Service Implementation Method")
    print("="*60)
    
    service_file = SERVICES_IMPL_PATH / "ClaimServiceImpl.java"
    print(f"\nParsing: {service_file}")
    
    parser = JavaParser(service_file)
    methods = parser.get_methods()
    
    # Find getClaims method
    target_method = None
    for method in methods:
        if method["name"] == "getClaims":
            target_method = method
            break
    
    if target_method:
        print(f"\n✓ Found method: {target_method['name']}")
        print(f"  Return type: {target_method['return_type']}")
        print(f"  Line number: {target_method['line_number']}")
        print(f"\n  Source code (first 30 lines):")
        print("  " + "-"*56)
        source = target_method.get('source_code', '')
        if source:
            for line in source.split('\n')[:30]:
                print(f"  {line}")
        else:
            print("  [NO SOURCE CODE EXTRACTED]")
        print("  " + "-"*56)
        
        # Test pattern matching
        print("\n  Testing pattern matching:")
        
        # Facade pattern
        facade_pattern = r'daoFacade\.(\w+)\s*\('
        matches = list(re.finditer(facade_pattern, source))
        
        if matches:
            print(f"  ✓ Found {len(matches)} facade call(s):")
            for match in matches:
                print(f"    - daoFacade.{match.group(1)}()")
        else:
            print("  ✗ No facade calls found")
    else:
        print("\n✗ Method 'getClaims' not found")
        print(f"\nSearching for methods containing 'claim' in name:")
        claim_methods = [m for m in methods if 'claim' in m['name'].lower()]
        for method in claim_methods[:10]:
            print(f"  - {method['name']}")

if __name__ == "__main__":
    debug_service_impl()
    debug_facade_method()
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
