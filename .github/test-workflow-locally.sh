#!/bin/bash

# Local workflow testing script
# This script simulates the workflow steps locally for testing

set -e

echo "🧪 Testing workflow steps locally..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Step 1: Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Step 2: Build database (default to about_singapore_law if no argument)
RESOURCE=${1:-about_singapore_law}
echo "🔨 Building database for resource: $RESOURCE"

if [ "$RESOURCE" = "all" ]; then
    uv run zeeker build
else
    uv run zeeker build "$RESOURCE"
fi

# Step 3: Validate database
echo "✅ Validating database..."
if [ ! -f "sglawwatch.db" ]; then
    echo "❌ Error: Database file not created"
    exit 1
fi

DB_SIZE=$(du -h sglawwatch.db | cut -f1)
echo "Database created successfully (${DB_SIZE})"

# Step 4: Database health check
echo "🏥 Running health checks..."
uv run python -c "
import sqlite3
import sys

try:
    conn = sqlite3.connect('sglawwatch.db')
    cursor = conn.cursor()
    
    # Get all non-system tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name NOT LIKE \"sqlite_%\"')
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f'Tables found: {tables}')
    
    total_records = 0
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'{table}: {count:,} records')
        total_records += count
    
    if total_records == 0:
        print('❌ Error: No data found in database')
        sys.exit(1)
        
    print(f'✅ Database validation passed: {total_records:,} total records')
    
    # Sample data check
    if 'about_singapore_law' in tables:
        cursor.execute('SELECT title FROM about_singapore_law LIMIT 3')
        samples = cursor.fetchall()
        print('Sample chapters:')
        for title, in samples:
            print(f'  - {title}')
    
except Exception as e:
    print(f'❌ Database validation failed: {e}')
    sys.exit(1)
"

# Step 5: Test deployment (dry run)
echo "🚀 Testing deployment configuration..."
if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✅ S3 credentials detected - deployment would proceed"
    echo "   Bucket: $S3_BUCKET"
    if [ -n "$S3_ENDPOINT_URL" ]; then
        echo "   Endpoint: $S3_ENDPOINT_URL"
    fi
    
    # Uncomment the next line to actually deploy
    # uv run zeeker deploy
    echo "   (Skipping actual deployment - uncomment line in script to deploy)"
else
    echo "ℹ️  S3 credentials not configured - deployment would be skipped"
    echo "   Set S3_BUCKET, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY to test deployment"
fi

echo ""
echo "🎉 All workflow steps completed successfully!"
echo ""
echo "Next steps:"
echo "- Commit your changes and push to repository"
echo "- Manually trigger workflows in GitHub Actions tab"
echo "- Monitor deployment summaries for data quality"
echo ""
echo "Manual workflow triggers (GitHub Actions tab):"
echo "- Deploy About Singapore Law Database > Run workflow"
echo "- Build and Deploy Sglawwatch Database > Run workflow"
echo "- Database Health Check > Run workflow (after deployments)"