echo "Starting application with waitress-serve..."
waitress-serve --threads 32 --listen="*:80" main:app