# CANON.md

> **The authoritative, immutable source of truth for EnterpriseSim.**
>
> This document defines **Meridian Commerce Group (MCG)** — a completely fictional
> Fortune 500 omnichannel retail enterprise created exclusively for the EnterpriseSim
> open-source project. MCG does not represent, and must not be confused with, any real
> organization. Any resemblance to a real company is coincidental.
>
> Every artifact in this repository — architecture documents, Jira issues, GitHub pull
> requests, release notes, business rules, incidents, test cases, knowledge documents,
> experience objects, evaluations and reflections — **must remain consistent with this
> canon**. When a conflict arises between any generated artifact and this document, this
> document wins. Changes to canon are versioned and recorded in the changelog at the
> bottom of this file.

| Field | Value |
|---|---|
| Canon ID | `CANON-001` |
| Canon Version | `1.0.0` |
| Status | **Authoritative / Locked** |
| Effective Date | 2026-01-01 |
| Enterprise | Meridian Commerce Group (MCG) |
| Project | EnterpriseSim — *The Open Benchmark for Enterprise AI Workers* |
| Domain | Omnichannel Retail (used only as a realistic backdrop) |
| Primary Objective | Simulate enterprise **software engineering** systems to build, evaluate and benchmark Enterprise AI Workers |

> **Design intent.** EnterpriseSim optimizes for **software-engineering realism**, not
> business realism. Retail is the domain that produces believable engineering artifacts;
> it is not the subject. The engineering organization should feel comparable in maturity
> to large cloud-native digital enterprises while remaining entirely fictional.

---

## Table of Contents

1. [Company](#1-company)
2. [Engineering Organization](#2-engineering-organization)
3. [Application Landscape](#3-application-landscape)
4. [Technology Standards](#4-technology-standards)
5. [Naming Conventions](#5-naming-conventions)
6. [ID Conventions](#6-id-conventions)
7. [Release Process](#7-release-process)
8. [Architecture Principles](#8-architecture-principles)
9. [Enterprise Worker Philosophy](#9-enterprise-worker-philosophy)
10. [Canon Change Log](#10-canon-change-log)

---

## 1. Company

### 1.1 Company History

Meridian Commerce Group was founded in **2004** in **Austin, Texas** as *Meridian
Marketplace*, an online marketplace connecting independent sellers with buyers across
North America. The founding thesis was that a technology company — not a retailer — would
win commerce by treating the storefront, the catalog and fulfillment as software systems.

A condensed engineering-relevant history:

| Era | Years | What happened (engineering lens) |
|---|---|---|
| **Marketplace origins** | 2004–2008 | Single Ruby/Rails monolith (`meridian-monolith`), one PostgreSQL database, deployed to leased data centers. Marketplace-only; no owned inventory. |
| **First-party retail** | 2009–2013 | Launched Meridian-owned inventory (1P) alongside 3P sellers. Split the monolith into first services (Catalog, Orders, Payments). Adopted Java for transactional services. |
| **Mobile & omnichannel** | 2014–2017 | Native iOS/Android apps. Acquired a regional brick-and-mortar chain, inheriting a legacy .NET POS estate (still in service, see APP-019). Began cloud migration to AWS. |
| **Cloud-native re-platform** | 2018–2021 | "Project Horizon" — decomposed remaining monolith into microservices, adopted Kubernetes, event-driven architecture (Apache Kafka), and a GitHub-centric SDLC. Stood up Platform Engineering. |
| **Data & AI platform** | 2022–2024 | Built the Enterprise Data Platform on a lakehouse (Databricks) with Snowflake for BI marts. Stood up AI Engineering. Launched the Retail Media Network. |
| **Enterprise AI Workers** | 2025–present | MCG began integrating autonomous and semi-autonomous AI Workers into the SDLC and operations. EnterpriseSim canonicalizes this environment. |

Two legacy facts are permanent canon and must be respected by all artifacts:

- The original **Rails monolith still exists in a reduced form** as the Marketplace Seller
  admin backend (see APP-018) and is actively being strangled.
- The **.NET POS estate (APP-019)** was acquired, not built, and carries integration debt.

### 1.2 Mission

> **"Make commerce a solved engineering problem for every seller and every customer,
> everywhere."**

MCG's operating belief is that retail outcomes (price, availability, delivery, trust) are
downstream of engineering quality. The company invests in platform, data and AI capability
as its primary competitive moat.

### 1.3 Business Model

MCG operates a **hybrid omnichannel model** with four revenue engines:

1. **First-party retail (1P):** MCG buys, owns and sells inventory through its digital and
   physical channels.
2. **Third-party marketplace (3P):** Independent sellers list and sell on MCG's platform;
   MCG earns commissions and fulfillment fees.
3. **Financial services:** Payments, digital wallet, gift cards, and the Meridian Rewards
   loyalty program.
4. **Retail media network:** Advertising sold to brands and sellers against MCG's
   audience and shopping data.

### 1.4 Geographic Presence

MCG operates in **seven countries** across three regions. Region codes are canonical and
used across configuration, feature flags and data partitioning.

| Region | Region Code | Countries | Primary Languages |
|---|---|---|---|
| North America | `NA` | United States (`US`), Canada (`CA`), Mexico (`MX`) | English, Spanish, French (CA) |
| Latin America | `LATAM` | Brazil (`BR`) | Portuguese |
| Europe | `EU` | United Kingdom (`GB`), Germany (`DE`) | English, German |
| Asia-Pacific | `APAC` | Australia (`AU`) | English |

Headcount: **~80,000 employees** total; **~4,500 in the Technology organization**.

### 1.5 Business Units

MCG is organized into six business units. The Technology BU is the sponsor and primary
subject of EnterpriseSim.

| BU ID | Business Unit | Charter |
|---|---|---|
| `BU-DIGITAL` | **Meridian Digital** | E-commerce web, mobile, marketplace consumer experience |
| `BU-RETAIL` | **Meridian Retail** | Physical stores, in-store technology, store operations |
| `BU-FIN` | **Meridian Financial Services** | Payments, wallet, gift cards, loyalty, MCG-branded credit |
| `BU-LOGISTICS` | **Meridian Logistics** | Fulfillment centers, warehouse, inventory, last-mile delivery |
| `BU-MEDIA` | **Meridian Media & Advertising** | Retail media network, sponsored placements |
| `BU-TECH` | **Meridian Technology** | Platform, data, AI, security and all engineering (owns EnterpriseSim) |

### 1.6 Product Portfolio

Customer- and seller-facing products (distinct from internal applications in §3):

| Product | Audience | Backing Applications (see §3) |
|---|---|---|
| **meridian.com** | Consumers | APP-001, APP-005, APP-006, APP-003 |
| **Meridian Mobile** (iOS/Android) | Consumers | APP-002 |
| **Meridian Marketplace** | Third-party sellers | APP-018 |
| **Meridian Rewards** | Loyalty members | APP-015 |
| **Meridian Pay & Wallet** | Consumers | APP-012, APP-013 |
| **Meridian Stores** (POS/in-store) | Store associates & shoppers | APP-019 |
| **Meridian Ads** | Brands & sellers | APP-022 |
| **My Meridian** (customer portal) | Registered customers | APP-021 |

---

## 2. Engineering Organization

### 2.1 Organization Structure

The Technology organization (`BU-TECH`) is led by the **Chief Technology Officer**. Below
the CTO are **Engineering Domains** (product-aligned, own applications and services) and
**Horizontal Functions** (Platform, Security, Quality, Data, AI — provide capabilities and
standards to every domain).

```
                          Chief Technology Officer
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
  Engineering Domains        Horizontal Functions          Architecture Office
  (own products/services)    (own platforms/standards)     (owns CANON, ADRs, RFCs)
        │                            │
  ┌─────┴─────┐              ┌────────┼────────┬────────┬────────┐
  DOM-STORE   DOM-COMMERCE   Platform  DevSecOps  QE      Data    AI
  DOM-PRICING DOM-PAYMENTS   Eng       (SEC)      Eng     Eng     Eng
  DOM-FULFIL  DOM-CUSTOMER  (PLAT)               (QE)   (DATA)  (AIENG)
  DOM-DATA-AI
```

Each domain is composed of **squads** (7–9 engineers, one Engineering Manager, one Product
Owner, one embedded QE, on-call rotation). A squad owns one or more services end to end.

### 2.2 Teams

Canonical team registry (referenced by `TEAM-###` and by ownership metadata everywhere):

| Team ID | Team Name | Function | Owns (examples) |
|---|---|---|---|
| `TEAM-001` | Storefront Experience | DOM-STORE | APP-001, APP-021 |
| `TEAM-002` | Mobile Platform | DOM-STORE | APP-002 |
| `TEAM-003` | Search & Discovery | DOM-STORE | APP-006 |
| `TEAM-004` | Cart & Checkout | DOM-COMMERCE | APP-003, APP-004 |
| `TEAM-005` | Catalog | DOM-COMMERCE | APP-005 |
| `TEAM-006` | Order Management | DOM-COMMERCE | APP-009 |
| `TEAM-007` | Pricing | DOM-PRICING | APP-007 |
| `TEAM-008` | Promotions & Offers | DOM-PRICING | APP-008 |
| `TEAM-009` | Payments | DOM-PAYMENTS | APP-012 |
| `TEAM-010` | Wallet & Gift Cards | DOM-PAYMENTS | APP-013 |
| `TEAM-011` | Loyalty | DOM-PAYMENTS | APP-015 |
| `TEAM-012` | Inventory | DOM-FULFIL | APP-010 |
| `TEAM-013` | Warehouse & Fulfillment | DOM-FULFIL | APP-011 |
| `TEAM-014` | Identity & Customer Profile | DOM-CUSTOMER | APP-014 |
| `TEAM-015` | Marketing Automation | DOM-CUSTOMER | APP-016 |
| `TEAM-016` | Customer Support Platform | DOM-CUSTOMER | APP-017 |
| `TEAM-017` | Marketplace Seller Platform | DOM-COMMERCE | APP-018 |
| `TEAM-018` | Store Systems | DOM-STORE | APP-019 |
| `TEAM-019` | Notifications | DOM-CUSTOMER | APP-023 |
| `TEAM-020` | Retail Media | DOM-DATA-AI | APP-022 |
| `TEAM-030` | Core Platform | PLAT | APP-024, shared platform |
| `TEAM-031` | Developer Experience (DevEx) | PLAT | CI/CD, golden paths |
| `TEAM-032` | Observability & SRE | PLAT | telemetry, incident tooling |
| `TEAM-040` | Security Engineering | SEC | DevSecOps tooling, IAM |
| `TEAM-050` | Quality Engineering | QE | TestRail, test frameworks |
| `TEAM-060` | Data Platform | DATA | APP-020 |
| `TEAM-070` | AI Engineering | AIENG | AI Workers, ML platform |
| `TEAM-090` | Architecture Office | ARCH | CANON, ADRs, RFCs |

### 2.3 Responsibilities & Ownership Model

MCG runs a strict **"you build it, you run it"** model:

- **Every service has exactly one owning squad.** Ownership is recorded in the service
  catalog and is non-negotiable; there are no unowned services.
- The owning squad is accountable for the service's **code, tests, deployment, on-call,
  SLOs, cost and documentation** across its full lifecycle.
- **On-call** is squad-local with a follow-the-sun escalation for Tier 0 services.
- Cross-cutting changes are coordinated through the **Architecture Office** (`TEAM-090`)
  via RFCs; standards are enforced through **golden paths**, not tickets.

### 2.4 Platform Engineering (`PLAT`)

Provides the paved road so product squads move fast safely. Deliverables:

- Kubernetes-based **internal developer platform** (self-service namespaces, service
  templates, "golden path" scaffolds).
- **CI/CD** pipelines, build caches, artifact registries (`TEAM-031` DevEx).
- **Observability** stack — metrics, logs, distributed tracing, SLO tooling — and the
  **incident management** toolchain (`TEAM-032` SRE).
- The **API Gateway / edge** (APP-024) and shared platform libraries.

### 2.5 Quality Engineering (`QE`)

Owns quality strategy, not just test execution:

- Test frameworks, test data management, and the **TestRail** test-case system of record.
- Quality gates in CI (coverage thresholds, contract tests, flaky-test quarantine).
- Embeds one QE per product squad; sets the **testing standard** (§4.4).

### 2.6 DevSecOps / Security Engineering (`SEC`)

- **Security by design**: threat modeling, secure-by-default templates, secrets
  management, SAST/DAST/SCA in every pipeline.
- **PCI-DSS** scope ownership for payments (APP-012) and cardholder-data boundaries.
- Identity & access management, workload identity, and vulnerability response.

### 2.7 Data Engineering (`DATA`)

- Owns the **Enterprise Data Platform** (APP-020): the lakehouse (Databricks), the
  Snowflake BI marts, ingestion, the semantic layer and data governance.
- Data contracts between producing services and the platform; data quality SLOs.

### 2.8 AI Engineering (`AIENG`)

- Builds and operates **Enterprise AI Workers** and the ML/AI platform (feature store,
  model registry, evaluation harness, agent runtime).
- Owns the **Knowledge → Experience → Evaluation → Reflection** machinery that
  EnterpriseSim exists to exercise (see §9).

---

## 3. Application Landscape

Every enterprise application is listed below with its purpose, owning team, key
dependencies, technology stack, criticality tier and repository. Criticality tiers:

- **Tier 0** — Revenue- or safety-critical; outage is a Sev1; strictest SLOs.
- **Tier 1** — Business-critical; degraded operation tolerable briefly.
- **Tier 2** — Important; supports operations but not on the checkout path.
- **Tier 3** — Internal/supporting.

| APP ID | Application | Purpose | Owner | Key Dependencies | Tech Stack | Tier | Repository |
|---|---|---|---|---|---|---|---|
| `APP-001` | Storefront Web | meridian.com consumer web experience | `TEAM-001` | APP-005, APP-006, APP-004, APP-007, APP-024 | Next.js/React, Node BFF, TypeScript | 0 | `mcg-storefront-web` |
| `APP-002` | Mobile App Platform | iOS & Android consumer apps | `TEAM-002` | APP-024 (GraphQL), APP-014, APP-004 | Swift, Kotlin, GraphQL BFF | 0 | `mcg-mobile-app` |
| `APP-003` | Checkout Service | Orchestrates checkout & order placement | `TEAM-004` | APP-004, APP-007, APP-012, APP-010, APP-009 | Java, Spring Boot | 0 | `mcg-checkout-service` |
| `APP-004` | Cart Service | Shopping cart state & pricing preview | `TEAM-004` | APP-005, APP-007, APP-008 | Go, Redis | 0 | `mcg-cart-service` |
| `APP-005` | Product Catalog | Canonical product & offer data | `TEAM-005` | APP-020 (feeds), Kafka | Java, PostgreSQL, OpenSearch | 0 | `mcg-catalog-service` |
| `APP-006` | Search & Browse | Product search, browse, recommendations | `TEAM-003` | APP-005, APP-020, APP-024 | Python, OpenSearch, Kafka | 0 | `mcg-search-service` |
| `APP-007` | Pricing Service | Base & regional price resolution | `TEAM-007` | APP-005, APP-020 | Java, PostgreSQL | 0 | `mcg-pricing-service` |
| `APP-008` | Promotions Engine | Offers, coupons, cart-level discounts | `TEAM-008` | APP-007, APP-015, Kafka | Kotlin, Spring Boot, Redis | 1 | `mcg-promotions-engine` |
| `APP-009` | Order Management (OMS) | Order lifecycle, fulfillment orchestration | `TEAM-006` | APP-010, APP-011, APP-012, Kafka | Java, Spring Boot, PostgreSQL | 0 | `mcg-oms` |
| `APP-010` | Inventory Service | Real-time available-to-promise inventory | `TEAM-012` | APP-011, Kafka | Go, PostgreSQL, Redis | 0 | `mcg-inventory-service` |
| `APP-011` | Warehouse Management (WMS) | Fulfillment center operations | `TEAM-013` | APP-010, APP-009 | Java, PostgreSQL | 1 | `mcg-wms` |
| `APP-012` | Payments Service | Payment authorization & capture (PCI) | `TEAM-009` | APP-013, external PSPs, APP-024 | Java, Spring Boot, PostgreSQL | 0 | `mcg-payments-service` |
| `APP-013` | Wallet & Gift Cards | Stored value, gift cards, refunds | `TEAM-010` | APP-012, APP-014 | Kotlin, PostgreSQL | 1 | `mcg-wallet-service` |
| `APP-014` | Identity & Customer Profile | AuthN/AuthZ, customer identity | `TEAM-014` | APP-024, Kafka | Go, OIDC/OAuth2, PostgreSQL | 0 | `mcg-identity-service` |
| `APP-015` | Loyalty (Meridian Rewards) | Points, tiers, rewards | `TEAM-011` | APP-014, APP-009, APP-020 | Java, PostgreSQL | 1 | `mcg-loyalty-service` |
| `APP-016` | Marketing Automation | Campaigns, segments, journeys | `TEAM-015` | APP-020, APP-023, APP-014 | Python, Airflow, Kafka | 2 | `mcg-marketing-automation` |
| `APP-017` | Customer Support Platform | Agent console, case management | `TEAM-016` | APP-009, APP-014, APP-012 | TypeScript, Node, PostgreSQL | 1 | `mcg-support-platform` |
| `APP-018` | Marketplace Seller Platform | 3P seller onboarding & management | `TEAM-017` | APP-005, APP-009, APP-012 | Ruby on Rails (legacy) + React | 1 | `mcg-seller-platform` |
| `APP-019` | POS / In-Store | Point of sale & in-store services | `TEAM-018` | APP-007, APP-010, APP-012, APP-015 | C#/.NET (edge) + Java (backend) | 0 | `mcg-store-pos` |
| `APP-020` | Enterprise Data Platform | Lakehouse, marts, semantic layer | `TEAM-060` | all services (ingestion) | Databricks/Spark, Snowflake, dbt | 1 | `mcg-data-platform` |
| `APP-021` | Customer Portal (My Meridian) | Account, orders, returns self-service | `TEAM-001` | APP-009, APP-014, APP-015 | React, Node BFF | 1 | `mcg-customer-portal` |
| `APP-022` | Retail Media / Ad Platform | Sponsored placements, ad serving | `TEAM-020` | APP-006, APP-020 | Scala, Spark, Go | 2 | `mcg-ad-platform` |
| `APP-023` | Notifications Service | Email/SMS/push transactional messaging | `TEAM-019` | APP-014, Kafka | Go, PostgreSQL | 1 | `mcg-notifications-service` |
| `APP-024` | API Gateway / Edge | Ingress, routing, authN, rate limiting | `TEAM-030` | APP-014 | Envoy/Kong, Go, Lua | 0 | `mcg-api-gateway` |

> **Dependency direction is canon.** Checkout (APP-003) depends on Payments (APP-012); the
> reverse must never appear in any artifact. When generating incidents, PRs or architecture
> changes, respect the dependency graph above.

---

## 4. Technology Standards

### 4.1 Git Branching

MCG uses **trunk-based development** with short-lived branches:

- `main` is always releasable and protected. Direct pushes are forbidden.
- Feature branches: `feature/<JIRA-KEY>-<short-slug>` (e.g., `feature/CHK-1421-guest-checkout`).
- Bugfix branches: `bugfix/<JIRA-KEY>-<short-slug>`.
- Hotfix branches: `hotfix/<INC-ID>-<short-slug>` cut from the release tag.
- Branches live **< 3 days**; large work is feature-flagged behind Platform's flag service.
- Release tags: `v<MAJOR>.<MINOR>.<PATCH>` per service (semantic versioning).

### 4.2 Pull Requests

- Every change lands via PR into `main`. No exceptions.
- PRs must: link a Jira issue, pass all required checks, and receive **≥1 approval** (**≥2**
  for Tier 0 services and any change touching PCI or auth code).
- **CODEOWNERS** enforces owning-squad review; cross-service changes require the dependent
  team's review.
- PR template requires: summary, linked issue, testing evidence, rollback plan, and risk
  tier. Squash-merge is the default; the PR title becomes the commit message.
- PRs should be **< 400 lines** of diff where practical; larger PRs require justification.

### 4.3 Release Management

See §7 for the full process. Standard: **progressive delivery** (canary → percentage
rollout → full) with automated rollback on SLO breach.

### 4.4 Testing

The MCG **test pyramid** and required gates (owned by `TEAM-050` QE):

| Layer | Requirement |
|---|---|
| Unit tests | Required; line coverage **≥ 80%** for Tier 0/1 services, ≥ 70% otherwise |
| Contract tests | Required between any producer/consumer pair (consumer-driven contracts) |
| Integration tests | Required for service boundaries and data contracts |
| End-to-end tests | Curated critical-journey suite (e.g., "guest checkout") in TestRail |
| Performance tests | Required for Tier 0 before major releases |
| Security tests | SAST/DAST/SCA gates on every pipeline (see §4.6) |

- **TestRail** is the system of record for test cases (`TC-#####`) and test runs (`TR-####`).
- Flaky tests are auto-quarantined and tracked as bugs; quarantine > 14 days is a Sev3.

### 4.5 CI/CD

- Every repo uses the Platform **golden-path pipeline**: `lint → build → unit → SAST/SCA →
  package → deploy(staging) → integration/contract → DAST → deploy(canary) → progressive
  rollout`.
- Pipelines are defined as code (GitHub Actions in `.github/workflows/`, Azure DevOps for
  the legacy .NET POS estate).
- Immutable, signed container images; provenance/SBOM attached to every build.
- **No manual production changes.** Everything is GitOps-driven and auditable.

### 4.6 Security

- **Security by design**: threat model required for new services and for changes to Tier 0
  or PCI scope.
- Mandatory pipeline gates: **SAST, DAST, SCA/dependency scanning, secret scanning,
  container/image scanning**. High/critical findings block release.
- Secrets live in the platform secret manager; never in code, config or logs.
- Least-privilege workload identity; all service-to-service calls are mutually
  authenticated. PCI cardholder data is isolated to APP-012's boundary.

### 4.7 Documentation

- Docs live **with the code** and in the appropriate `docs/` area of this repository.
- Every service has a **service README**, a **runbook**, and an **architecture page**.
- Significant decisions are recorded as **ADRs** (`ADR-###`); cross-team proposals as
  **RFCs** (`RFC-###`). Both reference CANON and prior ADRs/RFCs.
- Documentation is treated as a deliverable of every release, not an afterthought.

### 4.8 API Standards

- **API-first**: the contract (OpenAPI 3.x for REST, protobuf for gRPC, SDL for GraphQL) is
  designed and reviewed before implementation.
- REST resources are plural nouns; versioned via URL (`/v1/...`); backward-incompatible
  changes require a new major version and a deprecation window.
- All public APIs go through the Gateway (APP-024), are rate-limited, authenticated, and
  emit standard telemetry. Pagination, error envelopes and idempotency keys follow the
  shared API guidelines.
- Event schemas (Kafka) are registered in the schema registry and evolve
  backward-compatibly.

---

## 5. Naming Conventions

Consistency across these conventions is canon; generators must not deviate.

| Entity | Convention | Example |
|---|---|---|
| **Applications** | `APP-###`, display name `Meridian <Name>` / functional name | `APP-003` "Checkout Service" |
| **Repositories** | `mcg-<domain-or-app>-<type>` (kebab-case) | `mcg-checkout-service`, `mcg-data-platform` |
| **Microservices** | `<domain>-<capability>-svc` | `commerce-checkout-svc`, `pricing-resolver-svc` |
| **Jira projects** | 2–4 letter uppercase key per domain/app | `CHK`, `OMS`, `PAY`, `PRC`, `INV` |
| **Jira issues** | `<PROJECT-KEY>-<number>` | `CHK-1421`, `PAY-980` |
| **GitHub PRs** | Native `<repo>#<number>`; canonical index `PR-####` | `mcg-checkout-service#312` ↔ `PR-0312` |
| **Git branches** | `feature\|bugfix\|hotfix/<key-or-inc>-<slug>` | `feature/CHK-1421-guest-checkout` |
| **Releases** | `REL-<YYYY>-<###>`; service tag `v<semver>` | `REL-2026-014`, `v3.4.0` |
| **Incidents** | `INC-<YYYY>-<###>` with severity `Sev1..Sev4` | `INC-2026-007` (Sev1) |
| **Test cases** | `TC-#####` (TestRail); suites `TS-###`; runs `TR-####` | `TC-10231`, `TR-0442` |
| **Knowledge docs** | `KN-###` | `KN-045` |
| **Context objects** | `CTX-###` | `CTX-118` |
| **Plan objects** | `PLAN-###` | `PLAN-072` |
| **Experience objects** | `EXP-###` | `EXP-090` |
| **Evaluation objects** | `EVAL-###` | `EVAL-061` |
| **Reflection objects** | `REF-###` | `REF-033` |
| **Architecture Decision Records** | `ADR-###` | `ADR-012` |
| **RFCs** | `RFC-###` | `RFC-008` |

Notes:

- **Jira keys are realistic and per-project** (like a real Jira instance). A generic
  `JIRA-####` form may be used only as a cross-reference fallback when a domain is not yet
  assigned; the per-project key is always preferred and canonical once assigned.
- **GitHub PR numbers are per-repository** (as in real GitHub). EnterpriseSim additionally
  maintains a zero-padded global `PR-####` index for cross-artifact linking; both forms
  must resolve to the same PR.

---

## 6. ID Conventions

All IDs are **globally unique within their namespace**, zero-padded for stable sorting, and
**immutable once assigned** (IDs are never reused, even after deletion).

| Prefix | Namespace | Format | Example | Assigned by |
|---|---|---|---|---|
| `CANON-` | Canon document | `CANON-###` | `CANON-001` | Architecture Office |
| `BU-` | Business unit | `BU-<NAME>` | `BU-TECH` | Canon |
| `TEAM-` | Team / squad | `TEAM-###` | `TEAM-004` | Canon |
| `APP-` | Application | `APP-###` | `APP-003` | Canon |
| `SVC-` | Microservice | `SVC-####` | `SVC-0121` | Platform catalog |
| `REPO-` | Repository | `REPO-###` | `REPO-014` | Platform catalog |
| `ADR-` | Architecture Decision Record | `ADR-###` | `ADR-012` | Architecture Office |
| `RFC-` | Request for Comments | `RFC-###` | `RFC-008` | Architecture Office |
| `<KEY>-` | Jira issue | `<PROJECT>-<n>` | `CHK-1421` | Jira |
| `PR-` | Pull request (global index) | `PR-####` | `PR-0312` | GitHub / index |
| `REL-` | Release | `REL-<YYYY>-<###>` | `REL-2026-014` | Release Mgmt |
| `INC-` | Incident | `INC-<YYYY>-<###>` | `INC-2026-007` | SRE |
| `TC-` | Test case | `TC-#####` | `TC-10231` | TestRail |
| `TS-` | Test suite | `TS-###` | `TS-014` | TestRail |
| `TR-` | Test run | `TR-####` | `TR-0442` | TestRail |
| `KN-` | Knowledge document | `KN-###` | `KN-045` | AI Eng / Knowledge |
| `CTX-` | Context object | `CTX-###` | `CTX-118` | AI Worker runtime |
| `PLAN-` | Plan object | `PLAN-###` | `PLAN-072` | AI Worker runtime |
| `EXP-` | Experience object | `EXP-###` | `EXP-090` | AI Worker runtime |
| `EVAL-` | Evaluation object | `EVAL-###` | `EVAL-061` | Evaluation harness |
| `REF-` | Reflection object | `REF-###` | `REF-033` | AI Worker runtime |

**Cross-referencing rule:** Any artifact that mentions another artifact must use its
canonical ID (e.g., a release note references `CHK-1421`, `PR-0312`, `TC-10231`, `INC-2026-007`).
This referential integrity is the backbone of EnterpriseSim.

---

## 7. Release Process

### 7.1 Sprint Cadence

- **2-week sprints**, aligned across the organization on a shared calendar.
- Sprint artifacts (planning, review, retro) are canon inputs to Reflection (§9).
- Program increments span **6 sprints (1 quarter)** for roadmap alignment.

### 7.2 Release Cadence

- **Continuous delivery** is the default: services release independently, multiple times
  per day, via the golden-path pipeline and progressive delivery.
- A coordinated **fortnightly release train** (`REL-<YYYY>-<###>`) bundles notable,
  cross-service or customer-visible changes for communication and change management; it is
  a *coordination and narrative* artifact, not a deployment gate for independent services.
- Release numbering is sequential per calendar year (`REL-2026-001`, `REL-2026-002`, ...).

### 7.3 Hotfix Policy

- Triggered by a **Sev1/Sev2 incident** or a critical security finding.
- Cut a `hotfix/<INC-ID>-<slug>` branch from the affected release tag; minimal, targeted
  change; expedited review (still **≥1 approval**, **≥2** for Tier 0/PCI).
- Fast-tracked pipeline with mandatory security and smoke gates; forward-merged to `main`.

### 7.4 Rollback Policy

- Every release must ship with a documented rollback plan (enforced in the PR template).
- Automated rollback triggers on SLO breach during canary/progressive rollout.
- Database migrations are **backward-compatible / expand-contract** so rollback never
  requires a schema down-migration under fire.

### 7.5 Approval Workflow

| Change class | Required approvals | Additional gates |
|---|---|---|
| Standard (Tier 2/3) | 1 code review | CI green |
| Tier 0/1 service | 2 code reviews (incl. CODEOWNERS) | CI green, perf gate for Tier 0 |
| PCI / auth code | 2 reviews incl. Security Eng | Threat-model check, SAST/DAST |
| Hotfix | 1–2 (by tier) | Incident linked, smoke + security gates |
| Cross-service contract change | Owning + dependent team | Contract tests, RFC if breaking |

---

## 8. Architecture Principles

These nine principles govern every design decision and must be reflected in ADRs, RFCs and
architecture artifacts.

1. **Microservices** — Systems are decomposed into independently deployable services owned
   by a single squad, aligned to business capabilities.
2. **Event-Driven** — Services communicate asynchronously via Kafka where coupling and
   scale demand it; events are first-class, versioned, and backward-compatible.
3. **API-First** — Contracts are designed and reviewed before implementation; the contract
   is the source of truth (§4.8).
4. **Cloud-Native** — Containerized, orchestrated on Kubernetes, horizontally scalable,
   stateless where possible, with infrastructure as code. Primary cloud AWS, Azure for the
   legacy POS estate.
5. **Domain-Driven Design** — Bounded contexts map to domains and squads; ubiquitous
   language is shared; models don't leak across contexts.
6. **Observability** — Every service emits metrics, structured logs and distributed traces;
   SLOs are defined and monitored; you cannot operate what you cannot observe.
7. **Security by Design** — Threat modeling, least privilege, secure defaults and
   defense-in-depth are built in from the start, not bolted on (§4.6).
8. **AI-Ready** — Systems expose clean APIs, rich telemetry, and well-documented knowledge
   so Enterprise AI Workers can retrieve context, act, and learn (see §9). Every domain
   publishes machine-readable knowledge and experience.
9. **Open Standards** — Prefer open protocols and formats (OpenAPI, gRPC/protobuf,
   OpenTelemetry, CloudEvents, SPDX/SBOM) over proprietary lock-in.

---

## 9. Enterprise Worker Philosophy

EnterpriseSim exists to build, evaluate and benchmark **Enterprise AI Workers** — software
agents that operate inside MCG's engineering organization the way a skilled engineer would:
they read context, plan, act through real tools and artifacts, are evaluated, reflect, and
get better over time.

### 9.1 How AI Workers interact with MCG

An Enterprise AI Worker operates against the same artifacts and systems as human engineers:
GitHub repositories, Jira issues, Confluence/knowledge docs, TestRail, releases and
incidents. It does not receive privileged, out-of-band information. Its job is to accomplish
engineering work — implementing a Jira story, diagnosing an incident, hardening a service,
improving test coverage — while producing artifacts that respect this canon.

### 9.2 The Enterprise Worker Lifecycle

```
        Knowledge
            │
            ▼
        Context
            │
            ▼
        Planning
            │
            ▼
        Execution
            │
            ▼
        Evaluation
            │
            ▼
        Reflection
            │
            ▼
        Experience
            │
            ▼
   Continuous Improvement
            │
            └──────────────► (feeds back into Knowledge & Context)
```

This loop is the core philosophy of EnterpriseSim. Each stage is a first-class, identified
artifact type so that the entire reasoning process is inspectable and benchmarkable.

#### Stage 1 — Knowledge (`KN-###`)

The organization's durable, curated understanding: architecture docs, business rules,
runbooks, standards (this canon), API specs, and post-incident learnings. Knowledge is
**retrievable** (semantic + keyword search) and **cited**. It answers *"what is true about
MCG and how it works?"* Knowledge is authored by humans and AI Workers alike and reviewed
before it becomes canonical.

#### Stage 2 — Context (`CTX-###`)

The task-specific working set assembled for a particular job: the relevant subset of
knowledge, the target code, the linked Jira issue, related prior experiences, and current
system state. Context Engineering is the discipline of assembling **the right, minimal,
sufficient** context. It answers *"what does the Worker need in front of it, right now, to
do this task well?"* Each context object records exactly what was retrieved and why.

#### Stage 3 — Planning (`PLAN-###`)

An explicit, ordered plan derived from context: the steps, the target artifacts, the
expected changes, the tests to run, and the rollback strategy. Plans reference the Jira
issue, the affected `APP-`/`SVC-`, and the standards they must satisfy. A plan is a
commitment the Worker can be evaluated against. It answers *"what will I do, in what order,
and how will I know it worked?"*

#### Stage 4 — Execution

The Worker acts through real tools: it writes code, opens a **PR** against a `mcg-*` repo,
updates tests in TestRail, comments on the Jira issue, or executes a runbook step. Execution
produces concrete, canonical artifacts (`PR-####`, branch, commits, test runs `TR-####`)
that are inspectable and diffable. It answers *"do the work, as a professional engineer
would, leaving a real trail."*

#### Stage 5 — Evaluation (`EVAL-###`)

Structured judgment of the execution against the plan and MCG standards: did tests pass, did
CI gates hold, was coverage met, did it respect the dependency graph and architecture
principles, did it resolve the issue? Evaluation produces a scored, evidence-linked verdict
and is the substrate for **benchmarking** AI Workers. It answers *"how good was this work,
by objective, repeatable criteria?"*

#### Stage 6 — Reflection (`REF-###`)

The Worker (and the organization) reasons about *why* the outcome occurred: what went well,
what failed, what was missing from context, what the plan got wrong, and what should change
next time. Reflection converts raw outcomes into transferable lessons. It answers *"what did
we learn, and what would we do differently?"*

#### Stage 7 — Experience (`EXP-###`)

Reflections are distilled into durable, retrievable **experience objects**: reusable lessons
tied to situations ("when changing pricing during a promotion window, also verify
APP-008 cache invalidation"). Experience is retrieved during future **Context** assembly,
closing the loop. It answers *"what has MCG learned from doing this kind of work before?"*

#### Stage 8 — Continuous Improvement

Experience and validated new learnings are **promoted back into Knowledge and Context**,
raising the baseline for every future task. Standards evolve, runbooks improve, test
coverage grows, and the organization — and its AI Workers — measurably get better over time.
This is the flywheel EnterpriseSim is built to demonstrate and benchmark.

### 9.3 What "good" looks like

A high-performing Enterprise AI Worker, measured in EnterpriseSim, demonstrates strong
**knowledge retrieval**, **semantic search**, **experience retrieval**, **context
engineering**, **planning**, **evaluation**, **reflection** and **continuous learning** —
producing engineering artifacts indistinguishable in quality and consistency from those of a
senior MCG engineer, and improving across successive tasks.

---

## 10. Canon Change Log

All changes to canon are versioned. Canon is authoritative; artifacts follow canon.

| Version | Date | Author | Change |
|---|---|---|---|
| `1.0.0` | 2026-01-01 | Architecture Office (`TEAM-090`) | Initial canon. Established MCG enterprise profile, engineering organization, application landscape (APP-001…APP-024), technology standards, naming & ID conventions, release process, architecture principles, and the Enterprise Worker lifecycle. |

---

*End of CANON.md — `CANON-001`, version 1.0.0. This document is authoritative for the entire
EnterpriseSim repository.*
