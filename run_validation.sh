#!/bin/bash
# Quick validation script for copyVisit API

echo "=================================="
echo "Call Graph Validation for copyVisit"
echo "=================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating virtual environment..."
    source venv/Scripts/activate
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Run validation
echo ""
echo "Running validation..."
python test_api_validation.py ClaimService copyVisit

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Validation completed successfully!"
    echo "📄 Check output/validation_reports/ for detailed reports"
else
    echo ""
    echo "❌ Validation failed. Review the output above for details."
    exit 1
fi
