# DealFlow360 — Git Commit Standards

**Phase 458 Specification: Conventional Commits Standard**

---

## 1. Commit Message Structure

DealFlow360 enforces the **Conventional Commits 1.0.0** specification:

```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

---

## 2. Commit Types

| Type | Intent & Usage | Example |
| :--- | :--- | :--- |
| `feat` | New feature or roadmap phase implementation | `feat(discount): implement inventory-aware discount engine` |
| `fix` | Bug fix in backend, frontend, or database | `fix(auth): handle expired refresh token race condition` |
| `docs` | Documentation changes only | `docs(devops): add deployment guide and secret matrix` |
| `style` | Formatting, whitespace, semi-colons (no code logic changes) | `style(frontend): format tailwind class ordering in governance` |
| `refactor` | Code restructuring without fixing a bug or adding a feature | `refactor(db): optimize warehouse stock allocation query` |
| `perf` | Code change improving execution performance or query latency | `perf(api): add composite index on applied discounts` |
| `test` | Adding missing tests or correcting existing tests | `test(g25): add fail-safe production config test assertions` |
| `build` | Build system, dependency upgrades, or package scripts | `build(frontend): update next.js to 14.2.35` |
| `ci` | CI/CD configuration and GitHub Actions workflows | `ci(actions): add postgres 15 service container for pytest` |
| `chore` | Routine repository maintenance, .gitignore, licenses | `chore(repo): clean up build cache and update gitignore` |
| `revert` | Reverting a previous commit | `revert: revert "feat(quote): draft quote calculation"` |

---

## 3. Scopes Taxonomy

Use specific scopes matching DealFlow360 domain components:

- `auth`: Authentication, JWT, RBAC, sessions, cookies
- `customer`: Customer CRUD, tiers, intelligence, profiles
- `product`: Products, categories, pricing, margins, subscriptions
- `warehouse`: Warehouses, inventory, reservations, ATP, fulfillment
- `governance`: Discount ceilings, authority limits, validation engine
- `discount`: Discount intelligence, decision engine, applied ledger
- `devops`: Deployment, systemd, nginx, process management, secrets
- `api`: FastAPI routing, error handlers, middleware
- `ui`: Frontend application shell, components, styling, layout

---

## 4. Subject Line Rules

1. **Imperative Mood**: Use "add", "fix", "implement", not "added", "fixes", "implementing".
2. **Capitalization**: Lowercase first letter after type/scope.
3. **No Trailing Period**: Do not end the subject with a `.`.
4. **Length**: Maximum 72 characters.

---

## 5. Body & Breaking Changes

- **Body**: Explain the *why* and *what* of the change, non-obvious design rationale, and edge cases handled. Wrap at 72 characters.
- **Breaking Changes**: Prefix with `BREAKING CHANGE:` or append `!` to the type/scope (e.g. `feat(api)!: rename discount_rate to discount_percentage`).

---

## 6. Examples

### Good Feature Commit:
```text
feat(governance): implement discount decision engine

Orchestrate governance ceilings, actor limits, margin rules, and
5-factor risk scoring to deterministically generate APPROVED,
ADJUSTED, ESCALATION_REQUIRED, or REJECTED outcomes.

Closes #119
```

### Good Bugfix Commit:
```text
fix(inventory): prevent negative ATP balance during simultaneous reservations

Apply pessimistic row locking with SELECT FOR UPDATE on warehouse_stock
records to eliminate concurrency race conditions.
```

### Good CI Commit:
```text
ci(workflows): add multi-stage GitHub Actions pipeline

Configure automated backend testing with PostgreSQL 15 container,
frontend TypeScript typechecking, and production build validation.
```
