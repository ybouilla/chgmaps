#!/bin/sh
set -e


case "$MODE" in
  test)
    echo "Running tests..."
    exec pytest -v app/tests
    ;;
      
  pipeline)
    echo "Running pipeline..."
    echo "Running data generation..."
    python3 -m app.main_data_generation

    echo "Validating CSV..."
    python3 -m app.validate_csv

    echo "Initializing database..."
    PGPASSWORD=my_password psql -h db -U myuser -d licenses_db -f /app/app/sql/create.sql

    echo "Adding to database..."
    python3 -m app.add_database --db_host db

    echo "Running transformations (through python/ pandas)..."
    python3 -m app.transformation
    echo "Running transformations (through SQL)..."
    PGPASSWORD=my_password psql -h db -U myuser -d licenses_db -f /app/app/sql/req.sql

    echo "Done."
        ;;
    *)
        echo "Unknown MODE: $MODE"
        exit 1
        ;;
    esac
