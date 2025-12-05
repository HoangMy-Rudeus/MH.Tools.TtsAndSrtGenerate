# Documentation Map

This file provides a complete overview of all available documentation organized according to the Divio documentation system.

## Documentation Philosophy

This project follows the **[Divio documentation system](https://documentation.divio.com/)**, which organizes documentation into four categories based on user needs:

- **Tutorials**: Learning-oriented, step-by-step lessons
- **How-To Guides**: Problem-oriented, task-specific instructions
- **Reference**: Information-oriented, technical descriptions
- **Explanation**: Understanding-oriented, background and concepts

## Complete Documentation Structure

```
docs/
│
├── README.md                          # Main documentation entry point
├── DOCUMENTATION_MAP.md               # This file - complete documentation overview
│
├── tutorials/                         # 📚 LEARNING-ORIENTED
│   ├── README.md                      # Tutorials overview
│   ├── GETTING_STARTED.md             # Complete setup walkthrough (30-45 min)
│   └── QUICK_START_DOCKER.md          # Docker quick start (5-10 min)
│
├── how-to/                            # 🛠️ PROBLEM-ORIENTED
│   ├── README.md                      # How-to guides overview
│   ├── DOCKER_SETUP.md                # Docker configuration guide
│   ├── GENERATE_API_DOCS.md           # Generate OpenAPI/Swagger docs
│   ├── KAFKA_INTEGRATION.md           # Kafka messaging guide
│   └── CONTRIBUTING.md                # Contribution workflow
│
├── reference/                         # 📖 INFORMATION-ORIENTED
│   ├── README.md                      # Reference overview
│   ├── QUICK_REFERENCE.md             # Quick reference card
│   ├── PROJECT_SUMMARY.md             # Project overview
│   └── api/
│       └── API-REFERENCE.md           # Complete API documentation
│
└── explanation/                       # 💡 UNDERSTANDING-ORIENTED
    ├── README.md                      # Explanation overview
    ├── transaction-service-design.md    # Core design philosophy
    ├── TESTING_STRATEGY.md            # Testing approach
    ├── TRANSFORMATION_EXAMPLE.md      # Setup script before/after examples
    ├── adr/                           # Architecture Decision Records
    │   ├── 001-clean-architecture.md
    │   ├── 002-mediatr-cqrs.md
    │   ├── 003-postgresql-ef-core.md
    │   ├── 004-hybrid-caching.md
    │   └── 005-centralized-error-handling.md
    ├── architecture/
    │   └── architecture-diagrams.md   # Visual architecture
    └── guides/
        └── transaction-GUIDE.md         # Service-specific concepts

Root Documentation Files:
├── SETUP_GUIDE.md                     # Complete setup script documentation
├── QUICK_REFERENCE.md                 # Quick reference for setup scripts
├── UPDATE_SUMMARY.md                  # What changed in setup scripts v2.0
├── CLAUDE.md                          # AI assistant development guide
├── README.md                          # Project overview and quick start
├── setup-docs.ps1                     # PowerShell transformation script
└── setup-docs.sh                      # Bash transformation script
```

## Documentation by User Role

### New Developer
**Goal**: Get started and understand the basics

1. Start: [Setup Guide](../SETUP_GUIDE.md) - Transform the template
2. Quick setup: [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md)
3. Understand: [Architecture Diagrams](explanation/architecture/architecture-diagrams.md)
4. Learn workflow: [CLAUDE.md](../CLAUDE.md)

**Estimated time**: 1-2 hours

---

### Template User
**Goal**: Transform CustomService into a new service

1. Quick Reference: [Quick Reference Card](../QUICK_REFERENCE.md)
2. Complete Guide: [Setup Guide](../SETUP_GUIDE.md)
3. Examples: [Transformation Examples](explanation/TRANSFORMATION_EXAMPLE.md)
4. Updates: [What's New in v2.0](../UPDATE_SUMMARY.md)

**Estimated time**: 15-30 minutes

---

### Contributing Developer
**Goal**: Contribute code effectively

1. Setup: [Getting Started Guide](tutorials/GETTING_STARTED.md)
2. Workflow: [Contributing Guide](how-to/CONTRIBUTING.md)
3. Development: [CLAUDE.md](../CLAUDE.md) (commands, patterns)
4. Testing: [Testing Strategy](explanation/TESTING_STRATEGY.md)
5. Reference: [Quick Reference Card](reference/QUICK_REFERENCE.md)

**Estimated time**: 2-3 hours

---

### Software Architect
**Goal**: Understand design decisions and architecture

1. Overview: [Architecture Diagrams](explanation/architecture/architecture-diagrams.md)
2. Decisions:
   - [ADR 001: Clean Architecture](explanation/adr/001-clean-architecture.md)
   - [ADR 002: CQRS with MediatR](explanation/adr/002-mediatr-cqrs.md)
   - [ADR 003: PostgreSQL & EF Core](explanation/adr/003-postgresql-ef-core.md)
   - [ADR 004: Hybrid Caching](explanation/adr/004-hybrid-caching.md)
   - [ADR 005: Centralized Error Handling](explanation/adr/005-centralized-error-handling.md)
3. Design: [Service Design](explanation/transaction-service-design.md)

**Estimated time**: 3-4 hours

---

### API Consumer / Frontend Developer
**Goal**: Integrate with the service API

1. API Docs: [API Reference](reference/api/API-REFERENCE.md)
2. Generate Spec: [Generate API Docs](how-to/GENERATE_API_DOCS.md)
3. Quick Setup: [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md)
4. Reference: [Quick Reference Card](reference/QUICK_REFERENCE.md)

**Estimated time**: 1 hour

---

### DevOps Engineer
**Goal**: Deploy and maintain the service

1. Quick Start: [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md)
2. Docker Setup: [Docker Setup Guide](how-to/DOCKER_SETUP.md)
3. Commands: [CLAUDE.md](../CLAUDE.md) (Docker, migrations)
4. Architecture: [Architecture Diagrams](explanation/architecture/architecture-diagrams.md)

**Estimated time**: 1-2 hours

---

### QA Engineer / Tester
**Goal**: Test the service effectively

1. Getting Started: [Getting Started Guide](tutorials/GETTING_STARTED.md)
2. Testing Strategy: [Testing Strategy](explanation/TESTING_STRATEGY.md)
3. API Reference: [API Reference](reference/api/API-REFERENCE.md)
4. Test Commands: [CLAUDE.md](../CLAUDE.md) (Testing section)

**Estimated time**: 2 hours

---

## Documentation by Topic

### Architecture & Design

| Document | Category | Topic |
|----------|----------|-------|
| [Architecture Diagrams](explanation/architecture/architecture-diagrams.md) | Explanation | Visual architecture overview |
| [ADR 001: Clean Architecture](explanation/adr/001-clean-architecture.md) | Explanation | Layer separation, dependency rules |
| [ADR 002: CQRS with MediatR](explanation/adr/002-mediatr-cqrs.md) | Explanation | Command/query separation |
| [Service Design](explanation/transaction-service-design.md) | Explanation | Security design philosophy |

---

### Getting Started

| Document | Category | Topic |
|----------|----------|-------|
| [Getting Started Guide](tutorials/GETTING_STARTED.md) | Tutorial | Complete setup walkthrough |
| [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md) | Tutorial | Fast Docker-based setup |
| [CLAUDE.md](../CLAUDE.md) | Reference | Development commands |

---

### Development

| Document | Category | Topic |
|----------|----------|-------|
| [Contributing Guide](how-to/CONTRIBUTING.md) | How-To | Contribution workflow |
| [Kafka Integration](how-to/KAFKA_INTEGRATION.md) | How-To | Event-driven messaging with Kafka |
| [CLAUDE.md](../CLAUDE.md) | Reference | Commands, patterns, conventions |
| [Testing Strategy](explanation/TESTING_STRATEGY.md) | Explanation | Testing philosophy |

---

### Deployment & Operations

| Document | Category | Topic |
|----------|----------|-------|
| [Docker Setup Guide](how-to/DOCKER_SETUP.md) | How-To | Docker configuration |
| [Kubernetes Guide](../k8s/README.md) | How-To | K8s and Minikube deployment |
| [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md) | Tutorial | Docker quick start |

---

### API Integration

| Document | Category | Topic |
|----------|----------|-------|
| [API Reference](reference/api/API-REFERENCE.md) | Reference | Complete API specification |
| [Generate API Docs](how-to/GENERATE_API_DOCS.md) | How-To | Export OpenAPI/Swagger docs |

---

### Technical Decisions

| Document | Category | Topic |
|----------|----------|-------|
| [ADR 001: Clean Architecture](explanation/adr/001-clean-architecture.md) | Explanation | Architecture pattern choice |
| [ADR 002: CQRS with MediatR](explanation/adr/002-mediatr-cqrs.md) | Explanation | CQRS implementation |
| [ADR 003: PostgreSQL & EF Core](explanation/adr/003-postgresql-ef-core.md) | Explanation | Database and ORM choice |
| [ADR 004: Hybrid Caching](explanation/adr/004-hybrid-caching.md) | Explanation | Caching strategy |
| [ADR 005: Error Handling](explanation/adr/005-centralized-error-handling.md) | Explanation | Error handling approach |

---

## Quick Navigation

### By Time Available

**5 minutes**: [Quick Reference Card](reference/QUICK_REFERENCE.md)

**15 minutes**: [Quick Start with Docker](tutorials/QUICK_START_DOCKER.md)

**1 hour**: [Getting Started Guide](tutorials/GETTING_STARTED.md) + [API Reference](reference/api/API-REFERENCE.md)

**Half day**: Complete [Tutorials](tutorials/) + [How-To Guides](how-to/) + [CLAUDE.md](../CLAUDE.md)

**Full day**: All [Explanation](explanation/) docs + practice development

---

### By Learning Style

**Hands-on learner**: Start with [Tutorials](tutorials/)

**Problem solver**: Jump to [How-To Guides](how-to/)

**Conceptual thinker**: Begin with [Explanation](explanation/)

**Quick reference**: Use [Reference](reference/)

---

## Contributing to Documentation

To contribute or suggest improvements to documentation:

1. Read the [Contributing Guide](how-to/CONTRIBUTING.md)
2. Follow the Divio system principles
3. Place new docs in the appropriate category:
   - **Tutorials**: Teaching newcomers through hands-on examples
   - **How-To Guides**: Solving specific practical problems
   - **Reference**: Providing technical specifications
   - **Explanation**: Explaining concepts and decisions
4. Update this map when adding new documentation
5. Submit a pull request

---

## Documentation Principles

### Tutorials Should:
- Be learning-oriented
- Get the user started
- Be focused on learning outcomes
- Be reproducible
- Be concrete, not abstract
- Provide immediate feedback

### How-To Guides Should:
- Be goal-oriented
- Solve specific problems
- Provide a series of steps
- Be flexible
- Omit unnecessary explanation
- Be practical, not theoretical

### Reference Should:
- Be information-oriented
- Describe the machinery
- Be accurate and complete
- Be austere
- Be consistent
- Do nothing but describe

### Explanation Should:
- Be understanding-oriented
- Provide context
- Explain design decisions
- Discuss alternatives
- Make connections
- Be discursive

---

**Last Updated**: [DATE]

**Navigation**: [Home](README.md) | [Tutorials](tutorials/) | [How-To](how-to/) | [Reference](reference/) | [Explanation](explanation/)
