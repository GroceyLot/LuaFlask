#!/bin/bash

echo "Starting application with waitress-serve..."
waitress-serve --threads 9 --listen="*:80" main:app
