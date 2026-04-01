#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "Building PC Health API..."
go mod tidy
go build -o pc-health-api .

echo "Build complete: pc-health-api"
