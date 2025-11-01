"""
API Validation Test - Simplified Version

Provides a simple interface to validate any API's call graph accuracy.
Usage: python test_api_validation.py <ServiceName> <apiName>
Example: python test_api_validation.py ClaimService copyVisit
"""
import sys
import json
from pathlib import Path
from test_call_graph_accuracy import CallGraphAccuracyValidator


def validate_api(service_name: str, api_name: str):
    """Validate a specific API"""
    print(f"\n{'='*80}")
    print(f"Validating API: {service_name}.{api_name}")
    print(f"{'='*80}\n")
    
    validator = CallGraphAccuracyValidator()
    results = validator.validate_api(service_name, api_name)
    
    # Save detailed report
    output_dir = Path(__file__).parent / "output" / "validation_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / f"{service_name}_{api_name}_validation.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create human-readable report
    readable_file = output_dir / f"{service_name}_{api_name}_report.txt"
    with open(readable_file, 'w') as f:
        f.write(f"CALL GRAPH ACCURACY REPORT\n")
        f.write(f"API: {service_name}.{api_name}\n")
        f.write(f"{'='*80}\n\n")
        
        f.write(f"OVERALL ACCURACY: {results['overall_accuracy']:.1f}%\n\n")
        
        f.write(f"STATISTICS:\n")
        f.write(f"  - Total Nodes: {results['total_nodes']}\n")
        f.write(f"  - Total Edges: {results['total_edges']}\n")
        f.write(f"  - Method Coverage: {results['method_coverage']['coverage_percent']:.1f}%\n")
        f.write(f"  - SQL/HQL Queries: {results['query_coverage']['total_queries']}\n")
        f.write(f"  - DAO Nodes: {results['dao_validation']['total_dao_nodes']}\n")
        f.write(f"  - Conditional Branches: {sum(results['branch_validation'].values())}\n\n")
        
        if results['method_coverage']['missing']:
            f.write(f"MISSING METHODS ({len(results['method_coverage']['missing'])}):\n")
            for method in results['method_coverage']['missing']:
                f.write(f"  - {method}\n")
            f.write("\n")
        
        if results['errors']:
            f.write(f"ERRORS ({len(results['errors'])}):\n")
            for error in results['errors']:
                f.write(f"  - {error}\n")
            f.write("\n")
        
        if results['warnings']:
            f.write(f"WARNINGS ({len(results['warnings'])}):\n")
            for warning in results['warnings']:
                f.write(f"  - {warning}\n")
            f.write("\n")
        
        f.write(f"BRANCH COVERAGE:\n")
        for branch_type, count in results['branch_validation'].items():
            f.write(f"  - {branch_type}: {count}\n")
        f.write("\n")
        
        f.write(f"DAO OPERATIONS:\n")
        for op_type, count in results['dao_validation']['operations'].items():
            f.write(f"  - {op_type}: {count}\n")
    
    print(f"\n📄 Reports saved:")
    print(f"   - JSON: {report_file}")
    print(f"   - Text: {readable_file}")
    
    return results


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python test_api_validation.py <ServiceName> <apiName>")
        print("\nExamples:")
        print("  python test_api_validation.py ClaimService copyVisit")
        print("  python test_api_validation.py ClaimService getClaims")
        print("  python test_api_validation.py EmrService getPatientData")
        sys.exit(1)
    
    service_name = sys.argv[1]
    api_name = sys.argv[2]
    
    try:
        results = validate_api(service_name, api_name)
        
        print(f"\n{'='*80}")
        if results['success']:
            print("✅ VALIDATION PASSED")
            print(f"   Accuracy: {results['overall_accuracy']:.1f}%")
            print("   The call graph accurately represents the API logic.")
        else:
            print("⚠️  VALIDATION COMPLETED WITH ISSUES")
            print(f"   Accuracy: {results['overall_accuracy']:.1f}%")
            print("   Review the report for details.")
        print(f"{'='*80}\n")
        
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
