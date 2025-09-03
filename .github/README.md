# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated building and deployment of the sglawwatch-zeeker databases.

## Workflows

### 1. `deploy-about-singapore-law.yml`
**Purpose:** Specialized workflow for the `about_singapore_law` resource.

**Triggers:**
- **Manual trigger only:** Workflow dispatch with optional force rebuild

**Features:**
- Builds only the `about_singapore_law` resource
- Fast execution (typically 5-10 minutes)
- Detailed logging and validation
- S3 deployment with error handling
- Automatic backup creation after deployment

### 2. `build-and-deploy.yml` 
**Purpose:** Comprehensive workflow for all resources in the project.

**Triggers:**
- **Manual trigger only:** Workflow dispatch with resource selection

**Features:**
- Can build specific resources or all resources
- Comprehensive database validation
- Support for all environment variables
- Extended timeout (45 minutes)
- Detailed statistics and summaries
- Automatic backup creation after deployment

### 3. `backup-database.yml`
**Purpose:** Create date-based backup archives in S3.

**Triggers:**
- **Manual trigger only:** Workflow dispatch with optional date and dry-run

**Features:**
- Creates backups with specific dates or today's date
- Dry-run mode for testing without uploading
- Stores archives at `s3://bucket/archives/YYYY-MM-DD/`
- Automatically builds database if not present locally
- Lightweight and fast execution (< 15 minutes)

### 4. `health-check.yml`
**Purpose:** Validate deployed databases and monitor system health.

**Triggers:**
- **Manual trigger:** For on-demand health checks
- **Automatic trigger:** After successful deployments

**Features:**
- Downloads and validates deployed databases from S3
- Comprehensive health checks and data quality validation
- Reports on database statistics and freshness
- Alerts on issues or anomalies

## Setup Instructions

### 1. Required Secrets

Configure these secrets in your GitHub repository (`Settings > Secrets and variables > Actions`):

#### For S3 Deployment (Required)
```
S3_BUCKET=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
```

#### For Non-AWS S3 Services (Optional)
```
S3_ENDPOINT_URL=https://your-s3-endpoint.com
```

#### For API Integrations (Required for some resources)
```
JINA_API_TOKEN=your-jina-api-token
OPENAI_API_KEY=your-openai-api-key
```

### 2. S3 Bucket Setup

Your S3 bucket should have the following structure after deployment:
```
your-bucket/
├── latest/
│   └── sglawwatch.db          # Latest database
└── assets/
    └── databases/
        └── sglawwatch/
            └── metadata.json   # Database metadata
```

### 3. Manual Workflow Triggers

#### Deploy About Singapore Law Only
1. Go to `Actions` tab in your GitHub repository
2. Select `Deploy About Singapore Law Database`
3. Click `Run workflow`
4. Optionally check `Force full rebuild`

#### Deploy All Resources
1. Go to `Actions` tab in your GitHub repository  
2. Select `Build and Deploy Sglawwatch Database`
3. Click `Run workflow`
4. Optionally specify a specific resource name
5. Optionally check `Force full rebuild`

## Workflow Outputs

### Artifacts
- **Database file:** `sglawwatch.db`
- **Metadata:** `metadata.json`
- **Retention:** 7-14 days depending on workflow

### Deployment Summary
Each successful workflow run creates a summary showing:
- Database statistics (record counts, file size)
- Sample of processed data
- Deployment timestamp and trigger information

### S3 Deployment
- Database deployed to: `s3://your-bucket/latest/sglawwatch.db`
- Metadata deployed to: `s3://your-bucket/assets/databases/sglawwatch/metadata.json`

## Monitoring and Troubleshooting

### Common Issues

**1. Build Failures**
- Check API key validity (JINA_API_TOKEN, OPENAI_API_KEY)
- Verify website accessibility and HTML structure changes
- Review resource-specific error messages

**2. Deployment Failures**
- Verify S3 credentials and permissions
- Check S3 bucket exists and is accessible
- Ensure S3_ENDPOINT_URL is correct for non-AWS services

**3. Timeout Issues**
- Individual resources timing out: Check website response times
- Overall workflow timing out: Increase `timeout-minutes` value

### Notifications

Workflow status appears in:
- GitHub Actions tab with success/failure status
- Deployment summaries with detailed statistics
- Artifacts section with downloadable database files

### Best Practices

1. **Run builds regularly** to keep data current
2. **Review deployment summaries** for data quality changes  
3. **Test locally first** using the test script before deploying
4. **Check artifacts** if deployment fails but build succeeds
5. **Update API keys** before they expire to prevent failures
6. **Use health checks** after deployments to verify data integrity

## Development Workflow

1. **Local Development:**
   ```bash
   # Test locally first
   uv run zeeker build about_singapore_law
   
   # Verify database
   sqlite3 sglawwatch.db ".tables"
   ```

2. **Push to Repository:**
   - Workflow triggers automatically on resource file changes
   - Monitor Actions tab for build status

3. **Manual Deployment:**
   - Use workflow dispatch for immediate deployment
   - Useful for urgent updates or testing

4. **Backup Management:**
   - Each deployment automatically creates a dated backup in S3 archives
   - Use the `Backup Database to S3 Archives` workflow for on-demand backups
   - Support for specific dates and dry-run testing
   - Archives stored at: `s3://bucket/archives/YYYY-MM-DD/sglawwatch.db`

5. **Production Deployment:**
   - Run workflows manually as needed to keep data current
   - Check for any structural changes in source websites
   - Monitor database size and record count trends