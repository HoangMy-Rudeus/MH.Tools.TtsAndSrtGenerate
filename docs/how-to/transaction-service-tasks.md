# Transaction Service - Implementation Plan

## Complexity Level: 3 - Feature with Multiple Components

**Service**: Transaction Service  
**Estimated Timeline**: 8 weeks  
**Level Justification**: Multiple database tables with partitioning, scheduled jobs for recurring transactions, complex search/filter capabilities, event-driven integration with 4+ consumer services.

---

## 1. Context & Requirements

### Business Capability

**Transaction Recording & Management**: Core domain service for recording expenses and income, categorization, search/filter, recurring transactions, and receipt attachments.

### Database Schema

**Database**: `expensevault_transactions`

**Tables**:

1. **Transactions** (Primary entity)
   - Columns: id, walletId, userId, categoryId, type (expense/income/transfer), amount, currency, exchangeRate, description, date, notes, tags (TEXT[]), location (JSONB), receiptId, recurringTransactionId, createdAt, updatedAt, deletedAt (soft delete)
   - Indexes: walletId_date, userId_date, categoryId, type, date, tags (GIN), location (GIN), deletedAt (partial)
   - Partitioning: RANGE(date) - quarterly partitions
   - Constraints: amount > 0, type IN ('expense', 'income', 'transfer')

2. **RecurringTransactions** (Template entity)
   - Columns: id, walletId, userId, categoryId, type, amount, currency, description, frequency (daily/weekly/monthly/yearly), interval, startDate, endDate, nextOccurrence, isActive, createdAt, updatedAt
   - Indexes: walletId, userId, nextOccurrence (for scheduled jobs), isActive (partial)
   - Constraints: frequency IN ('daily', 'weekly', 'monthly', 'yearly'), interval > 0

3. **TransactionAttachments** (Link to Media Service)
   - Columns: id, transactionId (FK), mediaId (reference to Media Service), type (receipt/invoice/other), createdAt
   - Indexes: transactionId, mediaId

### Event Integration

**Events Produced**:

1. **transaction.created.v1**
   - Topic: transaction.created
   - Consumers: Wallet Service (balance updates), Budget Service (limit checks), Analytics Service (insights), Notification Service (alerts)
   - Payload: transactionId, walletId, userId, categoryId, type, amount, currency, description, date, tags, location, receiptId, createdAt

2. **transaction.updated.v1**
   - Topic: transaction.updated
   - Consumers: Wallet Service (balance recalculation), Budget Service, Analytics Service
   - Payload: transactionId, walletId, userId, updatedFields (old/new values), updatedAt
   - Critical: Amount changes require balance recalculation

3. **transaction.deleted.v1**
   - Topic: transaction.deleted
   - Consumers: Wallet Service (revert balance), Budget Service, Analytics Service
   - Payload: transactionId, walletId, userId, amount, type, deletedAt

4. **recurring.transaction.due.v1**
   - Topic: recurring.transaction.due
   - Consumers: Transaction Service (creates transaction), Notification Service
   - Payload: recurringTransactionId, walletId, userId, categoryId, type, amount, currency, description, dueDate

**Events Consumed**: None (Transaction Service produces events only)

### Architecture

- **Clean Architecture** with MediatR (CQRS pattern)
- **Framework**: .NET 10
- **Database**: PostgreSQL 17 (with partitioning)
- **Messaging**: Kafka (4 topics produced)
- **Caching**: Redis (optional for read-heavy queries)
- **Storage**: Integration with Media Service for receipt attachments

---

## 2. Technical Design

### Domain Layer

**Entities**:

- `Transaction` (aggregate root)
  - Properties: Id, WalletId, UserId, CategoryId, Type (enum), Amount (Money value object), Currency, ExchangeRate, Description, Date, Notes, Tags (list), Location (value object), ReceiptId, RecurringTransactionId, CreatedAt, UpdatedAt, DeletedAt
  - Methods: Create(), Update(), Delete() (soft delete), AddAttachment(), RemoveAttachment()

- `RecurringTransaction` (aggregate root)
  - Properties: Id, WalletId, UserId, CategoryId, Type (enum), Amount (Money value object), Currency, Description, Frequency (enum), Interval, StartDate, EndDate, NextOccurrence, IsActive, CreatedAt, UpdatedAt
  - Methods: Create(), Update(), Deactivate(), CalculateNextOccurrence()

- `TransactionAttachment` (entity)
  - Properties: Id, TransactionId, MediaId, Type (enum), CreatedAt
  - Methods: Create()

**Value Objects**:

- `Money`: Amount (decimal), Currency (string)
- `Location`: Latitude (double), Longitude (double), Address (string)

**Enums**:

- `TransactionType`: Expense, Income, Transfer
- `RecurrenceFrequency`: Daily, Weekly, Monthly, Yearly
- `AttachmentType`: Receipt, Invoice, Other

### Application Layer (CQRS)

**Commands**:

- `CreateTransactionCommand` / `CreateTransactionCommandHandler`
- `UpdateTransactionCommand` / `UpdateTransactionCommandHandler`
- `DeleteTransactionCommand` / `DeleteTransactionCommandHandler` (soft delete)
- `CreateRecurringTransactionCommand` / `CreateRecurringTransactionCommandHandler`
- `UpdateRecurringTransactionCommand` / `UpdateRecurringTransactionCommandHandler`
- `DeactivateRecurringTransactionCommand` / `DeactivateRecurringTransactionCommandHandler`
- `AddTransactionAttachmentCommand` / `AddTransactionAttachmentCommandHandler`

**Queries**:

- `GetTransactionByIdQuery` / `GetTransactionByIdQueryHandler`
- `GetTransactionsByWalletQuery` / `GetTransactionsByWalletQueryHandler` (with paging, date range, type filter)
- `GetTransactionsByUserQuery` / `GetTransactionsByUserQueryHandler` (with paging, date range, type filter)
- `SearchTransactionsQuery` / `SearchTransactionsQueryHandler` (tags, location, description, complex filters)
- `GetRecurringTransactionByIdQuery` / `GetRecurringTransactionByIdQueryHandler`
- `GetRecurringTransactionsByWalletQuery` / `GetRecurringTransactionsByWalletQueryHandler`
- `GetDueRecurringTransactionsQuery` / `GetDueRecurringTransactionsQueryHandler` (for scheduled job)

**DTOs**:

- `TransactionDto`, `CreateTransactionDto`, `UpdateTransactionDto`
- `RecurringTransactionDto`, `CreateRecurringTransactionDto`, `UpdateRecurringTransactionDto`
- `TransactionAttachmentDto`
- `TransactionFilterDto` (date range, type, tags, categoryId, minAmount, maxAmount)

**Validators** (FluentValidation):

- `CreateTransactionCommandValidator`: walletId/userId required, amount > 0, type enum valid, date not future
- `UpdateTransactionCommandValidator`: similar validations
- `CreateRecurringTransactionCommandValidator`: frequency enum valid, interval > 0, startDate required
- `SearchTransactionsQueryValidator`: date range valid, pagination limits

### Infrastructure Layer

**DbContext**:

- `TransactionDbContext`: 3 DbSets (Transactions, RecurringTransactions, TransactionAttachments)
- Entity configurations: indexes, constraints, partitioning setup
- Soft delete query filter: `query.Where(t => t.DeletedAt == null)`

**Repositories**:

- `ITransactionRepository` / `TransactionRepository`
  - Methods: GetByIdAsync(), GetByWalletAsync() (with filters), SearchAsync(), CreateAsync(), UpdateAsync(), DeleteAsync() (soft delete)
  - Partition-aware queries for date-range filters

- `IRecurringTransactionRepository` / `RecurringTransactionRepository`
  - Methods: GetByIdAsync(), GetByWalletAsync(), GetDueAsync() (nextOccurrence <= today && isActive), CreateAsync(), UpdateAsync(), DeactivateAsync()

- `ITransactionAttachmentRepository` / `TransactionAttachmentRepository`
  - Methods: GetByTransactionIdAsync(), CreateAsync(), DeleteAsync()

**Kafka Producer**:

- `IEventProducer` / `KafkaEventProducer`
  - Methods: PublishTransactionCreatedAsync(), PublishTransactionUpdatedAsync(), PublishTransactionDeletedAsync(), PublishRecurringTransactionDueAsync()
  - CloudEvents v1.0 format with proper serialization

**Background Job** (Hosted Service):

- `RecurringTransactionJob`: Checks for due recurring transactions every hour
  - Query: GetDueRecurringTransactionsQuery (nextOccurrence <= DateTime.UtcNow && isActive)
  - For each: Create transaction, publish recurring.transaction.due event, calculate next occurrence
  - Error handling: Log failures, retry logic, dead-letter queue for poison messages

### API Layer

**Controllers**:

- `TransactionsController`:
  - POST /api/transactions → CreateTransactionCommand
  - GET /api/transactions/{id} → GetTransactionByIdQuery
  - PUT /api/transactions/{id} → UpdateTransactionCommand
  - DELETE /api/transactions/{id} → DeleteTransactionCommand (soft delete)
  - GET /api/transactions/wallet/{walletId} → GetTransactionsByWalletQuery (with date range, type filter, paging)
  - GET /api/transactions/user/{userId} → GetTransactionsByUserQuery (with filters)
  - POST /api/transactions/search → SearchTransactionsQuery (complex filters: tags, location, description)

- `RecurringTransactionsController`:
  - POST /api/recurring-transactions → CreateRecurringTransactionCommand
  - GET /api/recurring-transactions/{id} → GetRecurringTransactionByIdQuery
  - PUT /api/recurring-transactions/{id} → UpdateRecurringTransactionCommand
  - DELETE /api/recurring-transactions/{id} → DeactivateRecurringTransactionCommand
  - GET /api/recurring-transactions/wallet/{walletId} → GetRecurringTransactionsByWalletQuery

- `TransactionAttachmentsController`:
  - POST /api/transactions/{transactionId}/attachments → AddTransactionAttachmentCommand
  - GET /api/transactions/{transactionId}/attachments → GetTransactionAttachmentsByTransactionIdQuery
  - DELETE /api/transaction-attachments/{id} → DeleteTransactionAttachmentCommand

**Middleware**:

- JWT authentication (validate userId from token)
- Request logging (Serilog)
- Exception handling (global exception handler)
- Rate limiting (per user/IP)

---

## 3. Implementation Phases

### Week 1: Project Setup & Database Schema

**Focus**: Initialize project structure, database setup, Docker Compose

**Tasks**:

- [x] Create solution and projects (Domain, Application, Infrastructure, API)
- [x] Add NuGet packages: EF Core 10, Npgsql, MediatR, FluentValidation, Confluent.Kafka, Serilog
- [x] Create database migration: Transactions, RecurringTransactions, TransactionAttachments
- [x] Setup partitioning: Create initial quarterly partitions (current year + 1 year ahead)
- [x] Create Docker Compose: PostgreSQL, Kafka, Zookeeper, Redis
- [x] Test connection and partition creation

**Deliverables**:

- Project structure with Clean Architecture
- Database schema with partitioning
- Docker Compose environment running

**Success Criteria**:

- Solution builds successfully
- Database migrations applied
- Partitions created and queryable
- Docker Compose stack healthy

### Week 2: Domain Layer

**Focus**: Core entities, value objects, enums, business logic

**Tasks**:

- [x] Create `Transaction` entity (with factory method Create())
- [x] Create `RecurringTransaction` entity (with CalculateNextOccurrence())
- [x] Create `TransactionAttachment` entity
- [x] Create `Money` value object (amount + currency)
- [x] Create `Location` value object (lat, lng, address)
- [x] Create enums: TransactionType, RecurrenceFrequency, AttachmentType
- [x] Write unit tests for domain logic (50+ tests)

**Deliverables**:

- Domain entities with business rules
- Value objects with validation
- Comprehensive unit tests

**Success Criteria**:

- All domain tests pass (50+ tests)
- Business rules enforced (amount > 0, valid enums, etc.)
- CalculateNextOccurrence() logic correct for all frequencies

### Week 3: Application Layer (Commands & Queries)

**Focus**: CQRS pattern with MediatR

**Tasks**:

- [x] Create commands: CreateTransaction, UpdateTransaction, DeleteTransaction (soft delete)
- [x] Create recurring commands: CreateRecurringTransaction, UpdateRecurringTransaction, DeactivateRecurringTransaction
- [x] Create attachment command: AddTransactionAttachment
- [x] Create queries: GetTransactionById, GetTransactionsByWallet, GetTransactionsByUser, SearchTransactions
- [x] Create recurring queries: GetRecurringTransactionById, GetRecurringTransactionsByWallet, GetDueRecurringTransactions
- [x] Create DTOs: TransactionDto, RecurringTransactionDto, TransactionAttachmentDto, TransactionFilterDto
- [x] Create validators: FluentValidation for all commands/queries (date validation, amount validation, enum validation)
- [x] Write unit tests for handlers (70+ tests)

**Deliverables**:

- 10+ commands and handlers
- 8+ queries and handlers
- DTOs with AutoMapper profiles
- FluentValidation validators

**Success Criteria**:

- All handler tests pass (70+ tests)
- Validators catch invalid input
- DTOs map correctly

### Week 4: Infrastructure Layer (EF Core, Kafka, Background Job)

**Focus**: Database access, event publishing, scheduled job

**Tasks**:

- [x] Create `TransactionDbContext` with entity configurations
- [x] Configure soft delete query filter: `.Where(t => t.DeletedAt == null)`
- [x] Create indexes: B-tree indexes (walletId_date, userId_date, categoryId, type, date), GIN indexes (tags, location), partial index (deletedAt)
- [x] Create repositories: TransactionRepository (partition-aware queries), RecurringTransactionRepository, TransactionAttachmentRepository
- [x] Create `KafkaEventProducer`: PublishTransactionCreatedAsync(), PublishTransactionUpdatedAsync(), PublishTransactionDeletedAsync(), PublishRecurringTransactionDueAsync()
- [x] Create `RecurringTransactionJob` (Hosted Service): Query due transactions, create transactions, publish events, calculate next occurrence
- [x] Configure CloudEvents v1.0 format for Kafka messages
- [x] Write integration tests: DbContext tests (70+ tests), Kafka producer tests (10+ tests), background job tests (10+ tests)

**Deliverables**:

- EF Core DbContext with partitioning support
- Repository implementations
- Kafka event producer with CloudEvents format
- Background job for recurring transactions

**Success Criteria**:

- All integration tests pass (90+ tests)
- Soft delete filter works correctly
- Partitions queried correctly for date ranges
- Events published to Kafka successfully
- Background job creates transactions on schedule

### Week 5: API Layer & Search/Filter

**Focus**: REST controllers, search optimization

**Tasks**:

- [x] Create `TransactionsController` (7 endpoints: POST, GET by id, PUT, DELETE, GET by wallet, GET by user, POST search)
- [x] Create `RecurringTransactionsController` (5 endpoints: POST, GET by id, PUT, DELETE, GET by wallet)
- [x] Create `TransactionAttachmentsController` (3 endpoints: POST, GET, DELETE)
- [x] Add middleware: JWT authentication, request logging (Serilog), exception handling, rate limiting
- [x] Implement search optimization: Complex filters (tags, location radius, description full-text, date range, amount range), pagination with cursor-based approach
- [x] Add Swagger/OpenAPI documentation
- [x] Write API integration tests (60+ tests)

**Deliverables**:

- 15+ REST endpoints
- Middleware pipeline configured
- Advanced search/filter capabilities
- Swagger documentation

**Success Criteria**:

- All API tests pass (60+ tests)
- JWT authentication works
- Search queries perform well (<500ms for 1M records)
- Swagger UI accessible

### Week 6: Testing & Quality Assurance

**Focus**: Comprehensive testing, architecture compliance

**Tasks**:

- [x] Write architecture tests (NetArchTest): Dependency rules (Domain → no deps, Application → Domain only, Infrastructure → Application/Domain)
- [x] Write end-to-end tests: Full transaction lifecycle (create → update → delete), recurring transaction generation, attachment upload
- [x] Performance tests: 1M transactions partitioned, search queries with complex filters, concurrent writes (100 req/sec)
- [x] Load testing: Kafka event throughput (1,000 events/sec), background job with 10,000 due recurring transactions
- [x] Security testing: Authorization checks (user can only access own transactions), input validation, SQL injection prevention
- [x] Write test documentation: Test plan, coverage report (target: >80%), known issues

**Deliverables**:

- Architecture tests (10+ tests)
- E2E tests (20+ tests)
- Performance tests (15+ tests)
- Load tests (10+ tests)
- Security tests (15+ tests)
- Test documentation

**Success Criteria**:

- All tests pass (250+ total tests)
- Code coverage >80%
- Performance meets targets (<500ms search, >100 req/sec)
- Security vulnerabilities addressed

### Week 7: Deployment & Documentation

**Focus**: Containerization, Kubernetes deployment, partition management

**Tasks**:

- [x] Create Dockerfile (multi-stage build with .NET 10 SDK)
- [x] Create Kubernetes manifests: Deployment (3 replicas), Service (ClusterIP), ConfigMap, Secret, HorizontalPodAutoscaler (CPU 70%)
- [x] Create partition management script: Automatic partition creation (3 months ahead), partition pruning (retain 2 years), monitoring for missing partitions
- [x] Setup CI/CD pipeline: GitHub Actions (build, test, docker build, push to registry, deploy to EKS)
- [x] Create operational documentation: Deployment guide, monitoring guide (Prometheus metrics, Grafana dashboards), troubleshooting runbook
- [x] Write API documentation: Usage examples, authentication guide, error codes
- [x] Performance tuning: Database index optimization, Kafka producer batching, connection pooling

**Deliverables**:

- Dockerfile and Kubernetes manifests
- Partition management automation
- CI/CD pipeline configured
- Complete documentation

**Success Criteria**:

- Docker image builds and runs successfully
- Kubernetes deployment healthy (3 replicas)
- Partitions auto-created and pruned
- CI/CD pipeline deploys to staging
- Documentation complete and reviewed

### Week 8: Creative Phases & Final Polish

**Focus**: Address complex design decisions, final optimizations

**Creative Phase 1: Partitioning Strategy** (2 days)

- Explore: Monthly vs quarterly partitions
- Decision: Quarterly partitions (balance between partition count and query performance)
- Implementation: Partition management automation, query optimization for date ranges

**Creative Phase 2: Recurring Transaction Algorithm** (2 days)

- Explore: Scheduled job frequency (hourly vs daily), generation strategy (on-demand vs batch), error handling (retry vs skip)
- Decision: Hourly job, batch generation, 3-retry with exponential backoff
- Implementation: Background job with retry logic, DLQ for poison messages

**Creative Phase 3: Search & Filter Optimization** (1 day)

- Explore: Full-text search (PostgreSQL built-in vs Elasticsearch), location search (PostGIS vs simple distance calculation)
- Decision: PostgreSQL full-text search (simpler), simple distance calculation (no PostGIS dependency)
- Implementation: Optimized search queries with GIN indexes

**Final Tasks**:

- [x] Code review and refactoring
- [x] Security audit (OWASP checklist)
- [x] Performance profiling and optimization
- [x] Update all documentation with final decisions
- [x] Prepare demo environment

**Deliverables**:

- Creative phase documentation (3 documents)
- Final code review report
- Security audit report
- Performance profiling report
- Production-ready service

**Success Criteria**:

- All creative decisions documented
- Code meets quality standards (SonarQube A rating)
- Security audit passed (no high/critical issues)
- Performance targets met (>100 req/sec, <500ms search)

---

## 4. Dependencies & Integration Points

### Internal Service Dependencies

- **User Service**: Validate userId exists (HTTP call or event-driven cache)
- **Wallet Service**: Validate walletId exists, publish events for balance updates
- **Category Service**: Validate categoryId exists (optional, can be null)
- **Media Service**: Validate receiptId/mediaId exists for attachments
- **Budget Service**: Consumer of transaction events (checks budget limits)
- **Analytics Service**: Consumer of transaction events (updates insights)
- **Notification Service**: Consumer of transaction events (sends alerts)

### External Dependencies

- **PostgreSQL 17**: Primary database with partitioning support
- **Kafka**: Event streaming for transaction events (4 topics)
- **Redis**: Optional caching for read-heavy queries (user transaction history)

### Event Integration

**Produces**:

1. transaction.created.v1 → Wallet Service, Budget Service, Analytics Service, Notification Service
2. transaction.updated.v1 → Wallet Service (balance recalculation), Budget Service, Analytics Service
3. transaction.deleted.v1 → Wallet Service (revert balance), Budget Service, Analytics Service
4. recurring.transaction.due.v1 → Transaction Service (creates transaction), Notification Service

**Consumes**: None (Transaction Service is an event producer only)

---

## 5. Success Metrics

### Performance Targets

- **Transaction creation**: <100ms P99 latency
- **Search queries**: <500ms P99 latency (with 1M+ transactions)
- **Throughput**: >100 transactions/sec sustained
- **Background job**: Process 10,000 due recurring transactions in <5 minutes
- **Kafka event publishing**: >1,000 events/sec

### Quality Targets

- **Test coverage**: >80% code coverage
- **Architecture compliance**: 100% (NetArchTest)
- **Security audit**: No high/critical issues (OWASP)
- **Code quality**: SonarQube A rating

### Reliability Targets

- **Partition availability**: 100% (auto-create partitions 3 months ahead)
- **Event delivery**: >99.9% success rate (with 3-retry policy)
- **Background job reliability**: >99.5% (with DLQ for poison messages)
- **Soft delete consistency**: 100% (query filter enforced at DbContext level)

---

## 6. Risk Assessment

### High Risks

1. **Partition Management Complexity**
   - Risk: Manual partition creation, missing partitions, query failures
   - Mitigation: Automated partition creation/pruning, monitoring for missing partitions, fallback to non-partitioned queries

2. **Recurring Transaction Job Failures**
   - Risk: Job crashes, missed generations, duplicate transactions
   - Mitigation: Idempotent transaction creation (check for existing transaction with recurringTransactionId + dueDate), retry logic, DLQ for failures, monitoring

3. **Event Ordering Issues**
   - Risk: Wallet balance updates out of order (transaction.updated arrives before transaction.created)
   - Mitigation: Use walletId as Kafka partition key (ensures ordering per wallet), include sequence number in events

### Medium Risks

1. **Search Performance with Large Datasets**
   - Risk: Slow queries with 10M+ transactions
   - Mitigation: Quarterly partitioning, GIN indexes for tags/location, query optimization, Redis caching for hot data

2. **Soft Delete Complexity**
   - Risk: Forgot to filter deletedAt in queries, data leakage
   - Mitigation: Global query filter at DbContext level, architecture tests to enforce, code review checklist

### Low Risks

1. **Media Service Integration**
   - Risk: Receipt upload failures, orphaned media files
   - Mitigation: Background job to cleanup orphaned attachments, media service health checks

---

## 7. Open Questions & Decisions Needed

### Decisions Required Before Implementation

1. **Partitioning Frequency**: Monthly vs Quarterly partitions?
   - Recommendation: Quarterly (simpler management, fewer partitions, sufficient for 10M transactions)
   - Creative Phase 1 will explore this

2. **Recurring Transaction Job Frequency**: Hourly vs Daily?
   - Recommendation: Hourly (better user experience, timely transaction generation)
   - Creative Phase 2 will explore this

3. **Search Implementation**: PostgreSQL full-text search vs Elasticsearch?
   - Recommendation: PostgreSQL (simpler, no additional infrastructure)
   - Creative Phase 3 will explore this

4. **Location Search**: PostGIS extension vs simple distance calculation?
   - Recommendation: Simple distance calculation (no PostGIS dependency, sufficient for basic location search)
   - Creative Phase 3 will explore this

### Open Questions

1. Should we support bulk transaction import (e.g., CSV upload)?
   - Impact: Separate endpoint, validation, background job for large files
   - Decision needed: Week 3 (during application layer implementation)

2. Should we implement transaction categorization suggestions (ML-based)?
   - Impact: Integration with Analytics Service, ML model training
   - Decision needed: Week 5 (during API layer implementation)

3. Should we support transaction templates (not just recurring)?
   - Impact: New table, CRUD operations, UI support
   - Decision needed: Week 2 (during domain layer implementation)

---

## 8. Creative Phases Planning

### Creative Phase 1: Partitioning Strategy (Week 8, Day 1-2)

**Challenge**: Quarterly vs monthly partitions, partition management automation, query optimization

**Questions to Explore**:

1. What's the optimal partition size? (monthly = 12 partitions/year, quarterly = 4 partitions/year)
2. How do we handle queries spanning multiple partitions?
3. What's the automation strategy for partition creation/pruning?
4. How do we monitor partition health?

**Options to Compare**:

- **Option A**: Monthly partitions (finer granularity, more partitions, complex management)
- **Option B**: Quarterly partitions (simpler, fewer partitions, balance between query performance and management)
- **Option C**: Yearly partitions (simplest, but large partition sizes, slower queries)

**Success Criteria**:

- Partition management fully automated
- Query performance <500ms for date ranges
- Monitoring alerts for missing partitions

### Creative Phase 2: Recurring Transaction Algorithm (Week 8, Day 3-4)

**Challenge**: Scheduled job frequency, generation strategy, error handling

**Questions to Explore**:

1. What's the optimal job frequency? (hourly, daily, real-time)
2. How do we prevent duplicate transactions?
3. How do we handle failures? (retry, skip, DLQ)
4. How do we calculate next occurrence for different frequencies? (daily, weekly, monthly, yearly)

**Options to Compare**:

- **Option A**: Hourly batch job (good UX, manageable load, monitoring)
- **Option B**: Daily batch job (simpler, less frequent, delayed generation)
- **Option C**: Real-time event-driven (complex, immediate, potential for race conditions)

**Success Criteria**:

- No duplicate transactions
- >99.5% generation success rate
- <5 min to process 10,000 due transactions

### Creative Phase 3: Search & Filter Optimization (Week 8, Day 5)

**Challenge**: Full-text search, location search, performance with partitioned tables

**Questions to Explore**:

1. PostgreSQL full-text search vs Elasticsearch?
2. Location search: PostGIS vs simple distance calculation?
3. How to optimize queries with multiple filters? (indexes, query planning)
4. Should we use Redis caching for hot queries?

**Options to Compare**:

- **Option A**: PostgreSQL full-text search + simple distance (no additional infrastructure)
- **Option B**: Elasticsearch + PostGIS (powerful, but complex infrastructure)
- **Option C**: Hybrid approach (PostgreSQL for simple, Elasticsearch for complex)

**Success Criteria**:

- Search queries <500ms P99
- Support for complex filters (tags, location, description, date range, amount range)
- Query performance scales with dataset size (1M → 10M transactions)

---

## 9. Monitoring & Observability

### Metrics to Track (Prometheus)

**Service Metrics**:

- `transaction_created_total` (counter, labels: type, walletId)
- `transaction_updated_total` (counter, labels: type)
- `transaction_deleted_total` (counter, labels: type)
- `transaction_search_duration_seconds` (histogram, labels: filter_type)
- `transaction_creation_duration_seconds` (histogram)

**Background Job Metrics**:

- `recurring_transaction_job_run_total` (counter, labels: status)
- `recurring_transaction_generated_total` (counter)
- `recurring_transaction_job_duration_seconds` (histogram)
- `recurring_transaction_job_errors_total` (counter, labels: error_type)

**Database Metrics**:

- `transaction_db_query_duration_seconds` (histogram, labels: operation)
- `transaction_db_connection_pool_size` (gauge)
- `transaction_db_partition_count` (gauge)
- `transaction_db_partition_size_bytes` (gauge, labels: partition_name)

**Kafka Metrics**:

- `transaction_event_published_total` (counter, labels: event_type, status)
- `transaction_event_publish_duration_seconds` (histogram, labels: event_type)
- `transaction_event_publish_errors_total` (counter, labels: event_type, error_type)

### Alerts (Prometheus Alertmanager)

- **TransactionCreationLatencyHigh**: P99 latency >500ms for 5 minutes
- **RecurringJobFailed**: Recurring transaction job failed 3 consecutive times
- **MissingPartition**: Required partition missing (next quarter not created)
- **EventPublishFailureHigh**: Kafka event publish failure rate >1% for 5 minutes
- **DatabaseConnectionPoolExhausted**: Connection pool >90% utilized for 2 minutes

### Dashboards (Grafana)

1. **Transaction Service Overview**: Request rate, latency, error rate, active partitions
2. **Recurring Transaction Job**: Job runs, success rate, generation count, errors
3. **Database Performance**: Query latency, connection pool, partition sizes, slow queries
4. **Kafka Events**: Event publish rate, failure rate, latency, topic lag

---

## 10. Documentation Deliverables

### Technical Documentation

- [x] Architecture diagram (C4 model: Context, Container, Component)
- [x] Database schema diagram (ERD with partitioning strategy)
- [x] API documentation (Swagger/OpenAPI)
- [x] Event schema documentation (CloudEvents format)
- [x] Deployment guide (Kubernetes manifests, configuration)

### Operational Documentation

- [x] Monitoring guide (Prometheus metrics, Grafana dashboards, alerts)
- [x] Troubleshooting runbook (common issues, resolution steps)
- [x] Partition management guide (creation, pruning, monitoring)
- [x] Background job maintenance (job schedule, error handling, DLQ processing)

### Developer Documentation

- [x] Setup guide (local development with Docker Compose)
- [x] Testing guide (unit tests, integration tests, E2E tests)
- [x] Code standards (Clean Architecture, CQRS, naming conventions)
- [x] Contribution guide (Git workflow, code review checklist)

---

## 11. Final Checklist

### Before Production Deployment

- [ ] All tests pass (250+ tests, >80% coverage)
- [ ] Architecture tests enforce Clean Architecture rules
- [ ] Security audit completed (OWASP checklist, no high/critical issues)
- [ ] Performance tests meet targets (>100 req/sec, <500ms search)
- [ ] Load tests validated (1,000 Kafka events/sec, 10,000 recurring transactions in <5 min)
- [ ] Monitoring configured (Prometheus metrics, Grafana dashboards, alerts)
- [ ] Documentation complete (API docs, operational runbook, setup guide)
- [ ] Partition management automated (auto-create 3 months ahead, prune >2 years)
- [ ] CI/CD pipeline functional (GitHub Actions, Docker registry, EKS deployment)
- [ ] Disaster recovery tested (database backup/restore, partition recovery)

### Post-Deployment Monitoring

- [ ] Monitor service health (uptime >99.9%)
- [ ] Monitor transaction creation latency (P99 <100ms)
- [ ] Monitor search query performance (P99 <500ms)
- [ ] Monitor recurring job success rate (>99.5%)
- [ ] Monitor partition creation (partitions created 3 months ahead)
- [ ] Monitor Kafka event publishing (success rate >99.9%)
- [ ] Review error logs daily (identify patterns, fix issues)
- [ ] Weekly performance review (query optimization, index tuning)

---

## 12. Timeline Summary

| Week | Focus | Deliverables | Success Criteria |
|------|-------|--------------|------------------|
| 1 | Project Setup | Project structure, database schema, Docker Compose | Solution builds, partitions created |
| 2 | Domain Layer | Entities, value objects, enums, unit tests | 50+ tests pass, business rules enforced |
| 3 | Application Layer | Commands, queries, DTOs, validators, unit tests | 70+ handler tests pass, validators work |
| 4 | Infrastructure Layer | DbContext, repositories, Kafka producer, background job | 90+ integration tests pass, events published |
| 5 | API Layer | Controllers, middleware, search/filter, Swagger | 60+ API tests pass, search <500ms |
| 6 | Testing & QA | Architecture tests, E2E tests, performance tests, security tests | 250+ total tests pass, >80% coverage |
| 7 | Deployment | Dockerfile, Kubernetes, partition management, CI/CD | Docker image builds, K8s healthy, CI/CD works |
| 8 | Creative Phases | Partitioning strategy, recurring algorithm, search optimization | All creative decisions documented, production-ready |

**Total Timeline**: 8 weeks  
**Total Tests**: 250+ tests  
**Total Documentation**: 10+ documents

---

*Generated by Copilot*
