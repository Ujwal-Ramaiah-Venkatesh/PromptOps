# PromptOps Critical Enhancements - Quick Reference

**Last Updated:** 2026-04-30

## Visual Architecture with Enhancements

```
┌─────────────────────────────────────────────────────────────────┐
│  PM Dashboard (Web UI)                                          │
│  • Command input                                                │
│  • 🎯 NEW: Autonomy Tier Settings (pre-authorize low-risk)     │
│  • 💰 NEW: Prompt-to-Billing View (cost per feature)           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  NLP Intent Engine (Claude Sonnet 4)                            │
│  • Parse commands • Risk assessment                             │
│  • 🎯 NEW: Check Autonomy Tier → Auto-execute if allowed       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Context & Memory Layer (DynamoDB)                              │
│  • Infrastructure state • Drift detection                       │
│  • 🔄 NEW: Infrastructure Ingestion (import manual changes)     │
│  • 🔍 NEW: Discovery Engine (map existing infrastructure)      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Execution Agents                                                │
│  • Deploy • Scale • Rollback • Monitor                          │
│  • 🔒 NEW: Secrets Agent (generate, rotate, inject)            │
│  • 💰 NEW: Cost Tagging (every resource tagged with op-id)     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Infrastructure (AWS, GCP, Azure)                          │
│  • 🔒 NEW: AWS Secrets Manager (integrated)                     │
│  • 💰 NEW: Cost Explorer (prompt-level attribution)             │
└─────────────────────────────────────────────────────────────────┘
```

## Enhancement Cheat Sheet

### 1. Autonomy Tiers 🎯

**When:** Phase 1 Q2 (Months 4-6)

**Quick Setup:**
```python
# PM configures in dashboard
autonomy_settings = {
    "low_risk": "auto_execute",      # Pod restarts, disk cleanup
    "medium_risk": "require_approval", # Staging deploys
    "high_risk": "require_approval",   # Prod deploys
    "critical": "multi_tier_approval"  # Schema changes
}
```

**Impact:** 95% of incidents auto-resolved without PM approval

---

### 2. Infrastructure Ingestion 🔄

**When:** Phase 1 Q3 (Months 7-9)

**Drift Detected Flow:**
```
1. 15-min drift check detects mismatch
2. Show PM three options:
   - [Import Change] ← NEW (update Terraform state)
   - [Revert Change] (undo manual change)
   - [Ignore Once] (suppress 24h)
3. If import: Architect Agent generates Terraform code
4. PM approves → State synchronized
```

**Impact:** Emergency fixes preserved, single source of truth maintained

---

### 3. Discovery & Onboarding 🔍

**When:** Phase 1 Q4 (Months 10-12)

**4-Week Sprint:**
```
Week 1: Scan AWS account (read-only)
Week 2: Auto-tag + dependency mapping
Week 3: Import selected resources into Terraform
Week 4: Validate + greenlight for new deploys
```

**Output:**
- Infrastructure map (all resources discovered)
- Dependency graph (relationships mapped)
- Cleanup recommendations (orphaned resources)
- Cost savings opportunities (idle instances)

**Impact:** Onboard messy existing accounts, not just greenfield

---

### 4. Prompt-to-Billing 💰

**When:** Phase 1 Q4 (Months 10-12)

**How It Works:**
```python
# Every command gets operation ID
command = "Deploy Search API"
operation_id = "op-20260415-search-api"

# Tag all resources
aws.ec2.tag(instance_id, {
    "promptops:operation": operation_id,
    "promptops:pm": "sarah.chen@company.com",
    "promptops:date": "2026-04-15"
})

# Query costs
monthly_cost = cost_explorer.get_cost_by_tag(operation_id)
# → $823/month for Search API
```

**Dashboard View:**
```
Top Cost Drivers:
1. Search API (Sarah Chen) - $823/month
2. Database Scale (Mike Johnson) - $420/month
3. Staging Env (Sarah Chen) - $310/month
```

**Impact:** Feature-level cost visibility for CFO

---

### 5. Secret Lifecycle 🔒

**When:** 
- Basic: Phase 1 Q2 (Months 4-6)
- Full: Phase 2 Q2 (Months 16-18)

**Flow:**
```python
# PM: "Deploy PostgreSQL database"

# PromptOps executes:
1. Generate secure password (32 chars, random)
   password = secrets.token_urlsafe(32)

2. Store in Secrets Manager
   aws.secretsmanager.create_secret(
       Name="promptops/db/password",
       SecretString=password,
       KmsKeyId="arn:aws:kms:...",
       RotationLambdaARN="arn:aws:lambda:..."
   )

3. Inject reference (NOT plaintext)
   terraform:
     password = data.aws_secretsmanager_secret_version.db.secret_string

4. Auto-rotate every 30 days
   Lambda rotation function (zero downtime)

5. PM never sees plaintext password ✓
```

**Compliance:**
- ✅ SOC2: Secrets encrypted + rotated
- ✅ HIPAA: Audit trail of access
- ✅ ISO 27001: Least-privilege access

**Impact:** Enterprise security out-of-box

---

## Implementation Priority

### Must Have (Phase 1)
1. ✅ **Autonomy Tiers** - Prevents alert fatigue
2. ✅ **Secrets Management** - Security/compliance blocker
3. ✅ **Infrastructure Ingestion** - Single source of truth

### High Value (Phase 1)
4. ✅ **Discovery Sprint** - Onboard existing customers
5. ✅ **Prompt-to-Billing** - CFO visibility

### Timeline

| Quarter | Months | Features |
|---------|--------|----------|
| Phase 1 Q2 | 4-6 | Autonomy Tiers + Secrets (basic) |
| Phase 1 Q3 | 7-9 | Infrastructure Ingestion |
| Phase 1 Q4 | 10-12 | Discovery Sprint + Cost Attribution |
| Phase 2 Q2 | 16-18 | Full Secret Lifecycle + Compliance Templates |

---

## Customer Value Props

### For PMs
- **Autonomy Tiers:** "No more 3 AM approval alerts for routine fixes"
- **Ingestion:** "Import your existing infrastructure, don't rebuild"
- **Cost Tracking:** "See exactly what each feature costs"

### For CFOs
- **Cost Attribution:** "Know which PM/feature drives AWS spend"
- **Discovery Sprint:** "Find $50K/year in wasted resources"
- **Secrets:** "SOC2/HIPAA compliant out-of-box"

### For DevOps (if still employed)
- **Autonomy Tiers:** "Configure what PMs can auto-execute"
- **Ingestion:** "Emergency console fixes don't break Terraform"
- **Audit Trail:** "Complete visibility into all changes"

---

## Technical Specs (High-Level)

### Database Schema Additions

```sql
-- Autonomy configuration
CREATE TABLE autonomy_tiers (
    user_id UUID,
    risk_level ENUM('low', 'medium', 'high', 'critical'),
    behavior ENUM('auto_execute', 'require_approval'),
    PRIMARY KEY (user_id, risk_level)
);

-- Operation cost tracking
CREATE TABLE operation_costs (
    operation_id VARCHAR(50) PRIMARY KEY,
    command TEXT,
    pm_email VARCHAR(255),
    created_at TIMESTAMP,
    estimated_monthly_cost DECIMAL(10,2),
    actual_monthly_cost DECIMAL(10,2),
    aws_tags JSONB
);

-- Infrastructure discovery
CREATE TABLE discovered_resources (
    resource_id VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(50),
    environment VARCHAR(20),
    tags JSONB,
    dependencies JSONB,
    discovered_at TIMESTAMP,
    imported BOOLEAN DEFAULT FALSE
);

-- Secrets metadata (NOT plaintext!)
CREATE TABLE managed_secrets (
    secret_name VARCHAR(255) PRIMARY KEY,
    secret_type VARCHAR(50),
    last_rotated_at TIMESTAMP,
    rotation_period_days INTEGER DEFAULT 30,
    next_rotation_at TIMESTAMP,
    aws_secret_arn VARCHAR(255)
);
```

### API Endpoints (New)

```
POST /api/v1/autonomy/configure
GET  /api/v1/autonomy/settings
POST /api/v1/ingestion/import-resource
GET  /api/v1/discovery/scan-account
GET  /api/v1/discovery/dependency-graph
GET  /api/v1/costs/by-operation
GET  /api/v1/costs/by-pm
POST /api/v1/secrets/rotate-now
GET  /api/v1/secrets/compliance-status
```

---

## Testing Checklist

### Autonomy Tiers
- [ ] PM configures low-risk as auto-execute
- [ ] Pod restart happens without approval
- [ ] Production deploy still requires approval
- [ ] Configuration persists across sessions

### Infrastructure Ingestion
- [ ] Manual AWS Console change detected
- [ ] Import option shown to PM
- [ ] Terraform code generated correctly
- [ ] State synchronized after import

### Discovery Sprint
- [ ] Scan discovers all existing resources
- [ ] Auto-tagging infers environments correctly
- [ ] Dependency graph shows relationships
- [ ] Import generates valid Terraform

### Prompt-to-Billing
- [ ] Resources tagged with operation ID
- [ ] Costs appear in dashboard within 24h
- [ ] PM can drill down to resource level
- [ ] CFO report shows feature-level costs

### Secret Lifecycle
- [ ] Database deployed without showing password
- [ ] Secret stored in AWS Secrets Manager
- [ ] ECS task reads from Secrets Manager
- [ ] Rotation works after 30 days (test with 1 min)
- [ ] Zero downtime during rotation

---

## Success Metrics

| Enhancement | Metric | Target |
|-------------|--------|--------|
| Autonomy Tiers | % incidents auto-resolved | >95% |
| Ingestion | % manual changes imported | >80% |
| Discovery | Time to onboard existing account | <4 weeks |
| Cost Attribution | CFO satisfaction score | >4.5/5 |
| Secrets | Compliance audit pass rate | 100% |

---

## Rollout Strategy

### Beta Testing (Month 4-6)
1. Enable for 10 pilot customers
2. Gather feedback on autonomy tier defaults
3. Validate cost attribution accuracy
4. Test secret rotation in staging

### General Availability (Month 7-9)
1. Roll out to all customers gradually
2. Monitor for issues
3. Iterate based on feedback
4. Document best practices

### Enterprise Features (Month 10-18)
1. Advanced compliance templates
2. Custom autonomy policies
3. Multi-account discovery
4. Advanced cost analytics

---

## FAQ

**Q: Do these features increase system complexity?**  
A: Initial implementation adds complexity, but simplifies PM experience. Net benefit: 6-9 month faster enterprise sales.

**Q: Can customers opt out?**  
A: Yes. Autonomy tiers default to "require approval for everything" (safe mode). PMs opt-in to auto-execution.

**Q: What if secret rotation fails?**  
A: Lambda keeps old password valid during rotation. If new password fails validation, rollback to old. Zero downtime guaranteed.

**Q: Does discovery work with GCP/Azure?**  
A: Phase 1: AWS only. Phase 2: GCP/Azure (months 13-18).

**Q: How accurate is cost attribution?**  
A: Within 5% (based on AWS Cost Explorer tags). More accurate than any manual tracking.

---

**Quick Reference Complete!**

For full details, see:
- [BLUEPRINT_ENHANCEMENTS_2026.md](BLUEPRINT_ENHANCEMENTS_2026.md) - Detailed specs
- [PromptOps_Complete_Blueprint_100percent_Automation.md](PromptOps_Complete_Blueprint_100percent_Automation.md) - Section 12.1
