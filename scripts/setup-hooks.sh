#!/bin/bash
# Git pre-commit hooks setup

# Ensure pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
