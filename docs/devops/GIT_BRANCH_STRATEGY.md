# DealFlow360 — Git Branch Strategy

**Phase 457 Specification: Practical Trunk-Based & Release Branching Model**

---

## 1. Core Principles

DealFlow360 follows a disciplined **Trunk-Based Development** workflow with dedicated short-lived feature branches, automated CI gates, and formal release tags.

```text
      (release-v1.0.0) ───[Tag: v1.0.0]
           /
master / main  ────────────────●──────────────────●─────── (Production Trunk)
           \                  /                  /
     feature/auth-jwt ───────┘                  /
                                               /
     hotfix/db-pool-timeout ──────────────────┘
```

---

## 2. Branch Hierarchy & Naming Conventions

| Branch Pattern | Lifetime | Base Branch | Merge Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `main` / `master` | Permanent | None | None | **Production baseline**. Always deployable, strictly protected. |
| `feature/<phase-or-feature>` | Short-lived | `master` | `master` | New roadmap phases or functionality (e.g. `feature/g25-devops`). |
| `bugfix/<issue-description>` | Short-lived | `master` | `master` | Non-urgent defects, corrections, and test hardening. |
| `hotfix/<incident-id>` | Short-lived | `master` | `master` | Critical production bug fixes requiring immediate deployment. |
| `release/v<x.y.z>` | Ephemeral | `master` | `master` | Final stabilization and tag preparation before production release. |

---

## 3. Branch Protection & PR Requirements

To preserve architectural integrity across all phases, the following rules apply to `master`:

1. **Pull Request Required**: Direct pushes to `master` are blocked in collaborative environments.
2. **Status Checks Must Pass**:
   - `backend-ci` (100% test pass on PostgreSQL, Alembic migrations verified).
   - `frontend-ci` (TypeScript typecheck passed, production build passed).
   - `devops-validation` (Nginx & systemd syntax validation).
3. **Linear History**:
   - Prefer **Squash and Merge** for feature branches to keep trunk history clean, atomic, and bisectable.
   - For major release branches, standard merge commits preserve detailed provenance.
4. **Clean Working Tree**:
   - Branches must be rebased on latest `master` before merge.

---

## 4. Release Tagging Convention

Production releases are marked with immutable annotated Git tags following **Semantic Versioning (SemVer 2.0)**:

```bash
# Format: v<Major>.<Minor>.<Patch>
git tag -a v0.1.0 -m "Release v0.1.0: Foundations G01–G25 complete"
git push origin v0.1.0
```

---

## 5. Developer Workflow Example

```bash
# 1. Ensure master is up to date
git checkout master
git pull origin master

# 2. Create topic branch
git checkout -b feature/g25-devops-deployment

# 3. Work and commit using conventional commits
git commit -m "feat(devops): configure nginx reverse proxy and systemd services"

# 4. Rebase and test locally before PR
git fetch origin master
git rebase origin/master
pytest tests
npm run typecheck
npm run build

# 5. Open Pull Request on GitHub
```
