#!/bin/bash

# Set PYTHONPATH to the project root
echo "Setting PYTHONPATH..."
export PYTHONPATH="$(pwd)"

echo "Running tests with coverage..."
# Run pytest with coverage, generating an HTML report
pytest --cov=APIs --cov=app --cov-report=html

# Open the coverage report even if some tests failed
echo "Opening coverage report..."
if command -v xdg-open &> /dev/null; then
    xdg-open htmlcov/index.html
elif command -v open &> /dev/null; then
    open htmlcov/index.html
else
    echo "Please open the coverage report manually: htmlcov/index.html"
fi
