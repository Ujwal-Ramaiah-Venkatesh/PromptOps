# ENHANCEMENT-003: Discovery & Onboarding Sprint

**Status:** 🚧 IN PROGRESS  
**Priority:** HIGH  
**Estimated Time:** 80 hours (2 weeks)  
**Phase:** Phase 1 Q3  
**Target Completion:** Week 16-18

---

## Problem Statement

**"The Day-2 Onboarding Problem"**

PromptOps is great for greenfield projects, but most teams have existing AWS infrastructure:
- 50+ EC2 instances across 3 environments
- RDS databases with complex configurations
- S3 buckets with unclear ownership
- Security groups with undocumented rules
- IAM roles created by 5 different engineers over 2 years

**Current Pain Points:**
1. **Manual Discovery:** Engineers must manually find and document each resource
2. **Unknown Dependencies:** Which ECS service depends on which RDS database?
3. **Missing Context:** Who owns this? What environment? What project?
4. **Import Complexity:** Converting AWS state to Terraform is tedious
5. **Incomplete Adoption:** Teams give up after importing 20% of resources

**Real-World Example:**
> "We spent 3 weeks trying to onboard our existing infrastructure into Terraform. We documented 40 EC2 instances, but gave up when we realized we also had 200+ S3 buckets, 15 RDS instances, and couldn't figure out which security groups were actually in use. We went back to manual AWS Console management."

---

## Solution Overview

**Automated Discovery & Intelligent Onboarding**

A read-only AWS scanner that:
1. **Discovers** all resources across all regions
2. **Infers context** (environment, project, owner) from tags and naming
3. **Maps dependencies** (this ECS service → that RDS database)
4. **Generates Terraform** for all discovered resources
5. **Presents actionable report** with one-click import

**Key Innovation:** Machine learning-style inference from existing patterns:
- If 80% of resources have `Environment: production` tag, infer missing ones from subnet/VPC
- If EC2 instances follow `app-env-number` naming, parse the pattern
- If resources share security groups, infer they're related

---

## Architecture

### Components

```
1. AWS Resource Scanner (Read-Only)
   └─ Multi-region discovery
   └─ Resource type detection (EC2, RDS, S3, etc.)
   └─ Relationship mapping
   
2. Context Inference Engine
   └─ Tag pattern analysis
   └─ Naming convention detection
   └─ Environment inference
   └─ Owner/project attribution
   
3. Dependency Graph Builder
   └─ Security group usage
   └─ Subnet/VPC relationships
   └─ IAM role attachments
   └─ Database connections
   
4. Discovery Report Generator
   └─ Resource inventory
   └─ Coverage analysis
   └─ Risk assessment
   └─ Import recommendations
   
5. Bulk Import Workflow
   └─ One-click import by environment
   └─ Terraform generation
   └─ Validation
   └─ State file creation
```

### System Flow

```
Step 1: DISCOVER
AWS Account → Scanner → Resource Inventory (JSON)
                ↓
        EC2, RDS, S3, VPC, IAM, etc.

Step 2: INFER CONTEXT
Resource Inventory → Context Engine → Enriched Inventory
                         ↓
        Environment, Project, Owner, Purpose

Step 3: MAP DEPENDENCIES
Enriched Inventory → Dependency Mapper → Dependency Graph
                            ↓
        ECS→RDS, Lambda→S3, EC2→SG

Step 4: GENERATE REPORT
Dependency Graph → Report Generator → Discovery Report UI
                         ↓
        "Found 247 resources: 60 EC2, 15 RDS, 120 S3..."
        "Inferred 3 environments: production, staging, dev"
        "Detected 5 projects: web-app, mobile-api, analytics..."

Step 5: BULK IMPORT
PM clicks "Import Production" → Generate Terraform → Apply to State
                                        ↓
        PromptOps now manages 247 resources ✅
```

---

## Implementation Tasks

### Task 1: AWS Resource Scanner (16 hours)

**File:** `phase1-nlp/discovery/aws_scanner.py`

**Features:**
- Read-only AWS API calls (no modifications)
- Multi-region scanning (parallel execution)
- Resource type support:
  - ✅ EC2 instances
  - ✅ RDS databases
  - ✅ S3 buckets
  - ✅ VPCs, subnets, security groups
  - ✅ ECS services, task definitions
  - ✅ Lambda functions
  - ✅ Load balancers (ALB, NLB)
  - ✅ IAM roles, policies
  - ✅ CloudFront distributions
  - ✅ Route53 hosted zones
- Rate limiting (avoid AWS throttling)
- Error handling (skip inaccessible resources)
- Progress tracking (scan 1/247 resources...)

**Code Structure:**
```python
class AWSScanner:
    def __init__(self, aws_credentials, regions):
        self.session = boto3.Session(...)
        self.regions = regions
        
    def scan_all_resources(self) -> ResourceInventory:
        """Scan all resources across all regions."""
        pass
        
    def scan_ec2_instances(self, region) -> List[EC2Resource]:
        """Scan EC2 instances in region."""
        pass
        
    def scan_rds_instances(self, region) -> List[RDSResource]:
        """Scan RDS databases in region."""
        pass
        
    # ... other resource types
```

**Output:** JSON file with all discovered resources

---

### Task 2: Context Inference Engine (20 hours)

**File:** `phase1-nlp/discovery/context_inference.py`

**Features:**
- **Tag Pattern Analysis**
  - Find common tags (Environment, Project, Owner, Cost-Center)
  - Detect tag consistency (80% have Environment tag → infer missing ones)
  
- **Naming Convention Detection**
  - Pattern recognition: `app-env-number` → `web-prod-1`, `web-prod-2`
  - Extract environment from name: `production-db`, `staging-api`
  
- **Environment Inference**
  - If resource in `subnet-prod-123` → likely production
  - If security group named `prod-sg` → production
  - If tags say `env: prod` → production
  
- **Owner/Project Attribution**
  - CloudTrail last-modified-by → owner
  - Tags (Owner, Team, Project)
  - Resource naming (team-app-env)
  
- **Purpose Detection**
  - Instance type suggests purpose: `t3.nano` = dev, `c5.4xlarge` = production
  - Database size suggests importance: 10GB = dev, 1TB = production

**Code Structure:**
```python
class ContextInferenceEngine:
    def infer_environment(self, resource: Resource) -> str:
        """Infer environment (production/staging/dev)."""
        # Check tags
        if 'Environment' in resource.tags:
            return resource.tags['Environment']
        
        # Check name
        if 'prod' in resource.name.lower():
            return 'production'
            
        # Check VPC/subnet
        if resource.subnet_id in self.production_subnets:
            return 'production'
            
        # Default
        return 'unknown'
        
    def infer_project(self, resource: Resource) -> str:
        """Infer project from tags/name."""
        pass
        
    def infer_owner(self, resource: Resource) -> str:
        """Infer owner from tags/CloudTrail."""
        pass
```

**Output:** Enriched resources with inferred context

---

### Task 3: Dependency Graph Builder (16 hours)

**File:** `phase1-nlp/discovery/dependency_mapper.py`

**Features:**
- **Security Group Dependencies**
  - EC2 instances → security groups
  - RDS databases → security groups
  - Detect which resources share security groups
  
- **Network Dependencies**
  - Resources in same VPC/subnet
  - Load balancer → target group → EC2 instances
  
- **IAM Dependencies**
  - EC2 instance → IAM role
  - Lambda function → IAM role
  - Role → policies
  
- **Application Dependencies**
  - ECS service → RDS database (inferred from security groups)
  - Lambda → S3 bucket (from environment variables)
  - EC2 → RDS (from security group rules)

**Code Structure:**
```python
class DependencyMapper:
    def build_dependency_graph(self, resources: List[Resource]) -> DependencyGraph:
        """Build graph of resource dependencies."""
        graph = DependencyGraph()
        
        # Map security group dependencies
        for resource in resources:
            if resource.type in ['ec2', 'rds']:
                for sg in resource.security_groups:
                    graph.add_edge(resource.id, sg)
        
        # Map network dependencies
        for resource in resources:
            if resource.subnet_id:
                graph.add_edge(resource.id, resource.subnet_id)
                graph.add_edge(resource.subnet_id, resource.vpc_id)
        
        return graph
        
    def detect_application_dependencies(self, graph: DependencyGraph) -> List[AppDependency]:
        """Infer application-level dependencies."""
        # ECS service → RDS (via shared security groups)
        # Lambda → S3 (from env vars)
        pass
```

**Output:** Dependency graph (JSON/GraphML format)

---

### Task 4: Discovery Report Generator (12 hours)

**File:** `phase1-nlp/discovery/report_generator.py`

**Features:**
- **Resource Inventory Report**
  - Total count by type
  - Breakdown by environment
  - Breakdown by project
  
- **Coverage Analysis**
  - Resources with complete tags: 60%
  - Resources with inferred context: 30%
  - Resources with unknown context: 10%
  
- **Risk Assessment**
  - Untagged production resources (HIGH risk)
  - Resources with no owner (MEDIUM risk)
  - Resources in default VPC (MEDIUM risk)
  
- **Import Recommendations**
  - Suggested import order (VPC → subnets → EC2 → RDS)
  - Resources to import by environment
  - Estimated import time

**Code Structure:**
```python
class DiscoveryReportGenerator:
    def generate_report(self, enriched_resources: List[Resource], 
                       dependency_graph: DependencyGraph) -> DiscoveryReport:
        """Generate comprehensive discovery report."""
        
        report = DiscoveryReport()
        
        # Count resources
        report.total_resources = len(enriched_resources)
        report.by_type = self._count_by_type(enriched_resources)
        report.by_environment = self._count_by_environment(enriched_resources)
        
        # Coverage analysis
        report.coverage = self._analyze_coverage(enriched_resources)
        
        # Risk assessment
        report.risks = self._assess_risks(enriched_resources)
        
        # Import recommendations
        report.import_plan = self._generate_import_plan(enriched_resources, dependency_graph)
        
        return report
```

**Output:** HTML/JSON report with visualizations

---

### Task 5: Discovery API Endpoints (8 hours)

**File:** `api_gateway/discovery_routes.py`

**Endpoints:**
```
POST   /api/v1/discovery/scan          - Start AWS discovery scan
GET    /api/v1/discovery/scan/{id}     - Get scan status
GET    /api/v1/discovery/report/{id}   - Get discovery report
POST   /api/v1/discovery/import        - Bulk import resources
GET    /api/v1/discovery/graph/{id}    - Get dependency graph
```

**Permissions:**
- Scan: engineers, leads, admins
- Import: leads, admins only

---

### Task 6: Discovery UI (16 hours)

**File:** `frontend/components/DiscoveryDashboard.tsx`

**Features:**
- **Scan Trigger**
  - "Start Discovery Scan" button
  - Progress indicator
  - Estimated time remaining
  
- **Resource Inventory View**
  - Table of all discovered resources
  - Filter by type, environment, project
  - Search by name/ID
  
- **Dependency Graph Visualization**
  - Interactive graph (d3.js or react-flow)
  - Click resource to see dependencies
  - Highlight related resources
  
- **Bulk Import Interface**
  - Checkbox selection by environment
  - "Import Production" button
  - Preview Terraform code
  - Confirm and execute

---

### Task 7: Database Schema (4 hours)

**File:** `database/migrations/009_add_discovery_tables.sql`

**Tables:**
```sql
-- Discovery scans
CREATE TABLE discovery_scans (
    id UUID PRIMARY KEY,
    scan_id VARCHAR(50) UNIQUE,
    initiated_by UUID NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(30),  -- running, complete, failed
    total_resources INTEGER,
    regions_scanned TEXT[]
);

-- Discovered resources
CREATE TABLE discovered_resources (
    id UUID PRIMARY KEY,
    scan_id VARCHAR(50),
    resource_id VARCHAR(255),
    resource_type VARCHAR(100),
    region VARCHAR(50),
    
    -- Raw AWS state
    aws_state JSONB,
    
    -- Inferred context
    inferred_environment VARCHAR(50),
    inferred_project VARCHAR(100),
    inferred_owner VARCHAR(255),
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    
    -- Import status
    imported BOOLEAN DEFAULT FALSE,
    imported_at TIMESTAMP,
    
    FOREIGN KEY (scan_id) REFERENCES discovery_scans(scan_id)
);

-- Resource dependencies
CREATE TABLE resource_dependencies (
    id UUID PRIMARY KEY,
    scan_id VARCHAR(50),
    source_resource_id VARCHAR(255),
    target_resource_id VARCHAR(255),
    dependency_type VARCHAR(50),  -- security_group, network, iam, application
    confidence_score DECIMAL(3,2)
);
```

---

### Task 8: Testing (8 hours)

**File:** `tests/test_discovery.py`

**Test Coverage:**
- AWS scanner mock tests
- Context inference accuracy tests
- Dependency detection tests
- Report generation tests
- API endpoint tests
- Bulk import workflow tests

---

## Success Metrics

**Completion Criteria:**
- [ ] Scans 10+ AWS resource types
- [ ] Discovers 95%+ of actual resources
- [ ] Correctly infers environment 85%+ of the time
- [ ] Detects 80%+ of security group dependencies
- [ ] Generates valid Terraform for all discovered resources
- [ ] Bulk import completes in <10 minutes for 250 resources
- [ ] UI displays dependency graph with <2 second load time

**Business Impact:**
- **Time Savings:** 3 weeks → 2 hours for infrastructure onboarding
- **Completeness:** 20% → 95% of resources managed
- **Adoption:** Teams actually complete onboarding instead of giving up

---

## Risk Mitigation

**Risks:**
1. **AWS API Rate Limits** → Implement exponential backoff, parallel scanning
2. **Large Accounts (1000+ resources)** → Pagination, streaming results
3. **Incomplete Inference** → Allow manual override, show confidence scores
4. **Import Failures** → Rollback capability, import one environment at a time

---

## Future Enhancements

**Phase 2 (Q4):**
- Multi-account discovery (AWS Organizations)
- Azure/GCP support
- Continuous discovery (daily scans, detect new resources)
- Cost analysis integration (show monthly cost per resource)
- Compliance checking (unencrypted RDS, public S3 buckets)

---

## Timeline

**Week 16: Foundation (32 hours)**
- Day 1-2: AWS Scanner implementation
- Day 3-4: Context Inference Engine

**Week 17: Graph & Reports (32 hours)**
- Day 1-2: Dependency Mapper
- Day 3-4: Report Generator + API

**Week 18: UI & Polish (16 hours)**
- Day 1-2: Discovery Dashboard UI
- Day 3: Testing & documentation

**Total:** 80 hours over 3 weeks

---

## Dependencies

**Prerequisites:**
- ✅ ENHANCEMENT-002 (Infrastructure Ingestion) - uses Terraform generator
- ✅ AWS credentials with read-only access
- ✅ boto3 library

**Blocked By:**
- None (can start immediately)

---

## Developer Notes

**AWS Permissions Required (Read-Only):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:Describe*",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "ecs:Describe*",
        "lambda:List*",
        "elasticloadbalancing:Describe*",
        "iam:List*",
        "iam:Get*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Performance Targets:**
- Scan 250 resources in <5 minutes
- Infer context for 250 resources in <30 seconds
- Build dependency graph in <1 minute
- Generate report in <10 seconds

---

**Next Steps:**
1. Create AWS scanner with EC2/RDS support
2. Implement tag pattern analysis
3. Build basic dependency detection
4. Create discovery API endpoint
5. Simple UI to trigger scan and view results
