# 📁 PromptOps Project Structure

Clean, organized project structure after cleanup on 2026-05-15.

---

## 📚 Root Documentation (Essential Only)

### Core Documentation
- **README.md** - Main project overview with features, quick start, and links
- **QUICK_START.md** - 5-minute setup guide
- **ARCHITECTURE.md** - System architecture and design
- **PRODUCT_OVERVIEW.md** - Product features overview

### Deployment
- **DEPLOYMENT.md** - Production deployment instructions
- **DEPLOYMENT_GUIDE.md** - Detailed deployment guide
- **AWS_FREE_TIER_SETUP.md** - AWS setup guide
- **AZURE_SETUP.md** - Azure setup guide
- **GCP_SETUP.md** - GCP setup guide

### Testing & Quality
- **TESTING_GUIDE.md** - Testing instructions
- **RUN_TESTS.md** - Test execution guide
- **SECURITY_AUDIT.md** - Security documentation

### Planning
- **NEXT_STEPS.md** - Future roadmap

### Reports
- **CLEANUP_REPORT.md** - This cleanup analysis (can be deleted after review)

---

## 🗂️ Project Directories

### Source Code
```
api_gateway/         - FastAPI backend server
frontend/            - React frontend application
  ├── dashboard/     - Main dashboard UI
  └── ...
database/            - Database schemas and migrations
config/              - Configuration files
scripts/             - Utility scripts
```

### Phase Directories (Implementation)
```
phase1-nlp/          - Natural language processing
phase2-aws/          - AWS integration
phase3-azure/        - Azure integration
phase3-gcp/          - GCP integration
phase4-ml/           - Machine learning features
phase5-enterprise/   - Enterprise features
phase5-mlops/        - MLOps integration
phase6-cicd/         - CI/CD pipeline
```

### Infrastructure
```
deployment/          - Deployment configurations
docker/              - Docker configurations
monitoring/          - Monitoring setup
alembic/             - Database migrations
logs/                - Application logs (gitignored)
```

### Documentation
```
docs/
├── PHASE1_BLUEPRINT.md
├── PROJECT_STATUS.md
├── UI_DESIGN_SPEC.md
├── WEEK1_CHECKLIST.md
└── archive/         - Historical files (140+ archived files)
    ├── deployment-status/
    ├── test-reports/
    ├── weekly-phase-reports/
    ├── enhancement-reports/
    ├── status-summaries/
    ├── temporary-scripts/
    ├── blueprint-docs/
    ├── large-reference-docs/
    ├── miscellaneous/
    ├── security-reports/
    └── directories/
```

---

## 🔧 Configuration Files

- **.gitignore** - Git ignore rules (updated to prevent future clutter)
- **.gitattributes** - Git attributes
- **.dockerignore** - Docker ignore rules
- **package.json** - Node.js dependencies
- **requirements.txt** - Python dependencies
- **docker-compose.yml** - Docker compose configuration
- **nginx.conf** - Nginx configuration
- **Dockerfile.api** - API Dockerfile
- **Dockerfile.backend** - Backend Dockerfile
- **Dockerfile.frontend** - Frontend Dockerfile
- **Dockerfile.context** - Context Dockerfile
- **.env.example** - Environment variables template

---

## 📊 Before vs After Cleanup

### BEFORE
- **180+ files** in root directory
- Cluttered with temporary status reports
- Multiple duplicate documentation files
- Hard to find essential docs
- Unprofessional appearance

### AFTER
- **18 files** in root directory (90% reduction!)
- Only essential documentation
- Clear, organized structure
- Easy to navigate
- Professional appearance

---

## 🗑️ What Was Archived

**140+ files moved to `docs/archive/`:**
- 31 deployment/build status files
- 14 test execution reports
- 28 weekly/phase completion reports
- 9 enhancement tracking files
- 5 security completion reports
- 18 status summaries
- 11 temporary scripts
- 9 blueprint generation files
- 6 large reference documents
- 18 miscellaneous files
- 2 directories (mobile-deployment/, utils/)

**Total archived: ~4.9 MB**

---

## 📝 Next Steps

### To commit these changes:
```bash
# Review what's changed
git status

# Add the cleanup changes
git add .

# Commit with a clear message
git commit -m "Clean up project structure

- Moved 140+ temporary files to docs/archive/
- Updated .gitignore to prevent future clutter
- Kept only essential documentation in root
- Reduced root files from 180+ to 18 (90% reduction)
- Added archive README for historical reference

Closes cleanup task"

# Push to remote
git push origin main
```

### Optional: Delete the archive
If you don't need historical reference, you can delete the archive:
```bash
rm -rf docs/archive/
git add docs/archive/
git commit -m "Remove archived historical files"
git push origin main
```

---

## 🎯 Project Navigation

### For Developers
1. Start with **README.md** for overview
2. Read **QUICK_START.md** for setup
3. Check **ARCHITECTURE.md** for design
4. See **TESTING_GUIDE.md** for testing

### For DevOps
1. Check **DEPLOYMENT.md** for deployment overview
2. Read **DEPLOYMENT_GUIDE.md** for detailed steps
3. Choose cloud: AWS_FREE_TIER_SETUP.md, AZURE_SETUP.md, or GCP_SETUP.md

### For Project Management
1. See **PRODUCT_OVERVIEW.md** for features
2. Check **NEXT_STEPS.md** for roadmap
3. Review **SECURITY_AUDIT.md** for security status

---

## ✅ Maintenance

### Keep Root Clean
The updated `.gitignore` now prevents:
- Status and progress reports
- Test execution logs
- Temporary build files
- Weekly/phase tracking files
- Temporary scripts
- Large blueprint documents

### Best Practices
- Keep only essential docs in root
- Use `docs/` for detailed documentation
- Archive old reports instead of deleting
- Update README.md as the single source of truth

---

**Last Updated**: 2026-05-15
**Structure Version**: 2.0 (Post-Cleanup)
