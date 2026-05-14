#!/bin/sh
set -e

echo "Starting Flask application..."
exec python -m app.run
