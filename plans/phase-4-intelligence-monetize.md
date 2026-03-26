# Phase 4: Intelligence + Monetize
**Timeline:** Weeks 15–24
**Goal:** Add a learning system that improves skill routing based on usage, launch AgentKit Pro (cloud), add enterprise features, and build the partner program for skill creators.

---

## Deliverables Checklist

- [ ] Learning system: routing improves from YOUR usage patterns
- [ ] Team analytics: cost-efficiency per developer, most valuable skills
- [ ] Custom skill creator wizard: describe → auto-generate SKILL.md
- [ ] Cloud sync: memory + config synced across machines
- [ ] Enterprise: RBAC, SSO, audit trails, spend limits per developer
- [ ] AgentKit Pro launch ($9/mo individual, $29/seat team)
- [ ] Partner program: skill creators earn revenue share from Pro bundles

---

## Week 15–17: Learning System

### 15.1 Usage Data Collection
**File:** `learning/collector.py`

Every session, anonymously collect (opt-in):
- Which skills were loaded vs actually used (activation vs relevance)
- Which model routing decisions were correct (did user override?)
- Which tasks failed quality gates (gate accuracy)
- Session cost before vs after (savings validation)

**Local usage log** (`.agentkit/usage.jsonl`):
```json
{"ts": 1743000000, "task": "debugging", "skills_loaded": ["debugging-python", "testing-tdd"], "skills_used": ["debugging-python"], "model": "sonnet", "model_correct": true, "gate_catches": 1, "cost": 0.23}
{"ts": 1743003600, "task": "api-work", "skills_loaded": ["api-rest", "auth-jwt"], "skills_used": ["api-rest", "auth-jwt"], "model": "haiku", "model_correct": false, "user_overrode_model": "sonnet", "cost": 0.04}
```

### 15.2 Personal Routing Model
**File:** `learning/personal_model.py`

After 100+ sessions, AgentKit builds a personal routing model for your usage patterns.

**What it learns:**

| Pattern | What it learns | Example |
|---------|---------------|---------|
| Task → Skills | Which skills you actually USE for each task type | "You debug Python 3x more than JS — load python-debugger first" |
| Prompt → Model | When Haiku vs Sonnet was the right call for you | "You write long specs — Haiku struggles, always use Sonnet" |
| Time → Cost | When you tend to go over budget | "Friday afternoon sessions run 2x longer — set budget alerts" |
| Files → Memory | Which files you revisit most | "You always re-read auth.py — inject it automatically" |

**Model storage** (`.agentkit/personal_model.json`):
```json
{
  "skill_weights": {
    "debugging": {
      "debugging-python": 0.92,
      "debugging-node": 0.34,
      "testing-tdd": 0.71
    },
    "api-work": {
      "api-rest": 0.88,
      "auth-jwt": 0.95,
      "api-graphql": 0.12
    }
  },
  "model_overrides": {
    "spec-writing": "sonnet",
    "file-search": "haiku"
  },
  "auto_inject_files": ["src/auth/jwt.py", "src/config/db.js"],
  "confidence": 0.84,
  "sessions_trained": 147
}
```

### 15.3 Continuous Improvement Loop

```
Session → Usage logged → Model updated → Next session routes better

Week 1:  Generic routing (baseline from Phase 1)
Week 4:  10% improvement in skill relevance
Week 8:  25% improvement in skill relevance
Week 12: Personal model fully calibrated (~85% routing accuracy)
```

---

## Week 17–19: Custom Skill Creator Wizard

### 17.1 Describe → Generate SKILL.md
**File:** `wizard/skill_creator.py`

Developer describes what they need → Haiku generates a complete SKILL.md.

**Wizard flow:**
```
$ npx agentkit skill create

Skill Creator Wizard
────────────────────
What does this skill help with?
> Prisma ORM with PostgreSQL — schema design, migrations, and query optimization

What are the top 3 things you always forget or get wrong with this?
> 1. How to handle optional relations in type-safe way
> 2. Migration rollback commands
> 3. N+1 query detection patterns

What platform do you use?
> [x] Claude Code  [x] Cursor  [ ] Codex  [ ] Gemini CLI

Generating skill...

✓ Created: skills/custom/prisma-postgres-expert.md
  Level 1: 48 tokens
  Level 2: 512 tokens
  Level 3: 2,180 tokens

Preview Level 2:
────────────────
## Prisma + PostgreSQL Expert
Activate for: Prisma schema design, migrations, queries, optimization

1. Optional relations: use `@relation(fields: [...], references: [...])` with `?`
2. Migration rollback: `npx prisma migrate resolve --rolled-back <migration_name>`
3. N+1 detection: check Prisma logs with `log: ['query']` in PrismaClient init
...

Publish to marketplace? [y/N]
```

### 17.2 Skill Quality Auto-Checker
**File:** `wizard/quality_checker.py`

Before any skill hits the marketplace, auto-check:

```python
SKILL_CHECKS = [
    ("has_level1",      lambda s: len(s.level1) < 80,        "Level 1 must be < 80 tokens"),
    ("has_level2",      lambda s: 400 < s.level2_tokens < 600,"Level 2 should be 400-600 tokens"),
    ("has_trigger",     lambda s: bool(s.trigger_keywords),    "Must have trigger keywords"),
    ("not_duplicate",   lambda s: not marketplace.has_similar(s), "Similar skill already exists"),
    ("platform_compat", lambda s: s.test_across_platforms(),   "Must work on 3+ platforms"),
]
```

---

## Week 19–21: AgentKit Pro — Cloud Features

### 19.1 Pro Tier Features ($9/mo)

**Cloud Sync:**
```
✓ Memory graph synced across all your machines
✓ Config synced (bundles, model routing, workflow settings)
✓ Personal routing model synced (doesn't reset on new machine)
✓ Custom skills synced
```

**Pro Skill Library (500+ skills):**
```
Free tier:  50 curated skills
Pro tier:   500+ skills including:
  - Domain expert packs (Stripe, AWS, Supabase, Vercel, etc.)
  - Language packs (Rust, Go, Elixir, Swift, Kotlin)
  - Framework packs (Rails, Django, FastAPI, Spring Boot)
  - Tool packs (Terraform, Pulumi, Ansible, ArgoCD)
```

**Advanced Analytics:**
```
- Session replay: see exactly what tokens cost what
- Skill ROI report: $/month saved by each skill
- Cost forecast: projected spend based on current pace
- Efficiency score: how you compare to optimal routing
```

**Custom Skill Creator Wizard:** (Pro-only)
```
- Generate skills from your codebase conventions
- "Learn from my past sessions" → auto-generate role-specific skills
- Team skill templates
```

### 19.2 Team Tier Features ($29/seat/mo)

**Shared Memory:**
```
Team members share the project knowledge graph.
When Alice discovers an API, Bob's agent knows it too.
Decisions made by senior devs propagate to the whole team.
```

**Developer Cost Analytics:**
```
Team Lead Dashboard:
  Alice    $34.20/mo  → efficiency 87%  → top skill: debugging-python
  Bob      $67.80/mo  → efficiency 61%  → suggestion: install api-rest skill
  Carol    $28.40/mo  → efficiency 93%  → most efficient developer

Team total: $130.40/mo (vs estimated $380/mo without AgentKit)
```

**Admin Dashboard:**
```
- Set spend limits per developer (e.g., $50/dev/month)
- Approve/block skill installations
- View audit log of all tool calls
- Slack/Teams notifications for cost alerts
```

**Shared Workflow Config:**
```yaml
# .agentkit-team.yaml (synced via cloud)
team_rules:
  - "Always use conventional commits"
  - "PR must reference Linear ticket"
  - "Tests required before merge"
enforce_methodology: true
quality_gates: [lint, typecheck, tests, security-scan]
```

### 19.3 Enterprise Tier ($99/seat/mo)

**SSO + RBAC:**
```
- SAML/OIDC SSO (Okta, Azure AD, Google Workspace)
- Role-based access: Admin, Developer, Viewer
- Per-team skill sets (frontend team can't use infra skills without approval)
```

**On-Prem Memory:**
```
- Memory graph hosted on customer's infrastructure
- No code leaves their environment
- Works air-gapped
```

**Audit Trail:**
```json
{
  "timestamp": "2026-03-26T10:30:00Z",
  "developer": "alice@acme.com",
  "action": "edit_file",
  "file": "src/auth/jwt.py",
  "model_used": "claude-sonnet-4-6",
  "cost": 0.042,
  "session_id": "sess_abc123",
  "skills_active": ["auth-jwt", "security-hardening"]
}
```

**Custom Skill Development:**
```
Enterprise customers get 10 custom skills developed by AgentKit team
Tailored to their codebase, stack, and conventions
Maintained + updated with platform changes
```

---

## Week 21–23: Partner Program

### 21.1 Skill Creator Revenue Share

Community skill creators earn revenue when their skills are included in Pro bundles.

**Revenue share model:**
```
Pro user installs "nextjs-app-router" skill:
  Monthly Pro fee:           $9.00
  Skill pack allocation:     30% = $2.70
  Skill's share of pack:     1/20 skills = $0.135/user/month

At 5,000 Pro users using the skill:
  Creator monthly revenue:   $675/month
  Annual:                    $8,100/year
```

**Partner tiers:**

| Tier | Requirements | Revenue Share | Benefits |
|------|-------------|--------------|---------|
| Contributor | 1 verified skill, 100+ downloads | 5% | Marketplace badge |
| Partner | 5 skills, 1000+ downloads, 4.5+ rating | 15% | Partner badge, early access |
| Elite Partner | 10 skills, 5000+ downloads, 4.8+ rating | 25% | Revenue share + co-marketing |

### 21.2 Skill Creator Tools

```
$ npx agentkit partner dashboard

Partner Dashboard: github:ajaysable
─────────────────────────────────────
Published Skills:    6
Total Downloads:     4,230
Avg Rating:         4.7 ⭐
Partner Tier:       Partner (15% revenue share)

Monthly Revenue:     $234.50
  nextjs-app-router: $145.20  (1,080 active Pro users)
  prisma-postgres:   $89.30   (664 active Pro users)

Payout date: April 1, 2026
```

---

## Week 23–24: AgentKit Pro Launch

### Launch Checklist

**Product:**
- [ ] Cloud sync working (memory + config)
- [ ] Pro skill library (500+ skills) live
- [ ] Payment via Stripe (monthly + annual)
- [ ] Team dashboard working
- [ ] Partner program live

**Marketing:**
- [ ] "Going Pro" blog post: "Why I monetized my open-source tool"
- [ ] Email list (built during open-source phase) notified
- [ ] Discord announcement in Claude Code Discord
- [ ] Twitter thread: "AgentKit Pro is live — here's what $9/mo gets you"
- [ ] Product Hunt re-launch as "AgentKit Pro"

**Pricing page copy:**
```
Community (Free)       Pro ($9/mo)           Team ($29/seat)
──────────────────     ─────────────────     ──────────────────
50 skills              500+ skills           Everything in Pro
Local memory           Cloud sync memory     Shared team memory
Self-hosted config     Cloud sync config     Team admin dashboard
Basic analytics        Advanced analytics    Developer cost tracking
                       Custom skill wizard   Spend limits per dev
                       Personal routing AI   Slack notifications
```

---

## Revenue Projections

| Period | Stars | Pro Users | Team Seats | MRR |
|--------|-------|-----------|------------|-----|
| Month 4-6 (waitlist) | 3K-10K | 0 | 0 | $0 |
| Month 7 (Pro launch) | 10K | 200 | 0 | $1,800 |
| Month 9 | 15K | 800 | 50 | $8,650 |
| Month 12 | 30K | 2,000 | 200 | $24,000 |
| Year 2 (Enterprise) | 60K+ | 5,000 | 1,000 | $100,000+ |

**Path to $100K MRR:**
```
5,000 Pro users × $9/mo     = $45,000
1,000 Team seats × $29/mo   = $29,000
200 Enterprise seats × $99  = $19,800
Partner program fees        = $6,200
                              ────────
Total MRR:                  = $100,000
```

---

## File Structure After Phase 4

```
agentkit/
├── [Phase 1-3 files...]
├── learning/
│   ├── collector.py          # usage data collection
│   ├── personal_model.py     # personal routing model
│   └── model_updater.py      # continuous improvement loop
├── wizard/
│   ├── skill_creator.py      # describe → generate SKILL.md
│   └── quality_checker.py    # skill quality auto-checker
├── pro/
│   ├── sync.py               # cloud sync (memory + config)
│   ├── auth.py               # Pro authentication
│   └── dashboard.py          # Pro analytics dashboard
├── enterprise/
│   ├── sso.py                # SAML/OIDC SSO
│   ├── rbac.py               # role-based access control
│   ├── audit.py              # audit trail
│   └── onprem.py             # on-prem memory storage
└── partner/
    ├── revenue.py            # revenue share calculation
    └── dashboard.py          # partner earnings dashboard
```

---

## Success Metrics for Phase 4

| Metric | Target |
|--------|--------|
| Pro conversion rate | 5-10% of active free users |
| Team conversion | 2% of active free teams |
| Skill routing accuracy (personal model) | > 85% |
| Partner skills in marketplace | 500+ |
| MRR at 24 weeks | $25,000+ |
| Churn rate (Pro) | < 5%/month |
| NPS | > 50 |
