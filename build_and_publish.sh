#!/bin/bash

# Remove dist folder if it exists
rm -rf dist

# Build package
uv build

# Publish to PyPI
uv publish
