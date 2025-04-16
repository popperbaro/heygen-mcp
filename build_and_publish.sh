#!/bin/bash

# Remove dist folder if it exists
rm -rf dist
rm -rf *.egg-info

# Build package
uv build

# Publish to PyPI
uv publish
