# Version Control & Traceability Plan - Mythological Forge

## Branching Strategy

### GitFlow Model with Semantic Branch Naming
- **`main`** - Production-ready code, protected branch requiring PR approval
- **`develop`** - Integration branch for features, updated frequently
- **`feature/*`** - Feature development branches (e.g., `feature/MF-123-archetypal-engine`)
- **`release/*`** - Release preparation branches (e.g., `release/v1.2.0`)
- **`hotfix/*`** - Emergency fixes for production (e.g., `hotfix/MF-456-critical-render-bug`)

### Branch Lifecycle
1. Create feature branches from `develop`: `git checkout -b feature/MF-XXX-description develop`
2. Merge features back to `develop` via PR after code review
3. Create release branches from `develop` when preparing releases
4. Merge releases to both `main` and `develop` after testing
5. Create hotfixes from `main`, merge to both `main` and `develop`

## Commit Message Convention

### Conventional Commits Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature implementation
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting (no logic changes)
- **refactor**: Code restructuring
- **perf**: Performance improvements
- **test**: Test additions or modifications
- **build**: Build system or dependency changes
- **ci**: CI/CD configuration changes
- **chore**: Maintenance tasks

### Examples
```
feat(myth-engine): implement recursive narrative generation

Added support for self-referential myth structures that can embed
sub-narratives within the main storyline. This enables creation of
myths with fractal-like narrative patterns.

Closes: MF-127
Related: MF-125, MF-126
```

```
fix(renderer): resolve sacred geometry rendering overflow

Fixed SVG viewport calculations that caused geometric symbols to
overflow container boundaries on mobile devices.

Fixes: MF-342
```

## Tagging & Release Management

### Semantic Versioning (SemVer)
- Format: `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`)
- **MAJOR**: Breaking API changes or major architectural shifts
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, minor improvements

### Release Process
1. Create release branch: `git checkout -b release/v1.2.0 develop`
2. Update `CHANGELOG.md` with release notes
3. Bump version in `package.json` and `requirements.txt`
4. Create annotated tag: `git tag -a v1.2.0 -m "Release version 1.2.0"`
5. Push tag: `git push origin v1.2.0`

### CHANGELOG.md Format
```markdown
# Changelog

## [1.2.0] - 2024-01-15

### Added
- Recursive narrative generation (MF-127)
- Support for custom archetypal templates (MF-130)

### Fixed
- Sacred geometry rendering on mobile (MF-342)
- Memory leak in myth caching system (MF-338)

### Changed
- Improved performance of element selection algorithm by 40%
- Updated dependencies to latest secure versions
```

## Traceability to Issues/Requirements

### Issue Reference Requirements
- **Every commit** must reference at least one issue ID
- Format: `MF-XXX` where XXX is the issue number
- Multiple issues: `MF-123, MF-124`

### Traceability Matrix
```
Feature Request → Issue (MF-XXX) → Branch → Commits → PR → Release
```

### PR Description Template
```markdown
## Summary
Brief description of changes

## Related Issues
Closes: MF-XXX
Related: MF-YYY, MF-ZZZ

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Code Review & Approval Process

### Review Requirements
- All PRs require **minimum 2 approvals** before merge
- Automated checks must pass:
  - Unit tests (>80% coverage)
  - Linting (ESLint, Flake8)
  - Security scan
  - Build verification

### Review Focus Areas
1. **Correctness**: Does the code solve the stated problem?
2. **Architecture**: Does it follow project patterns?
3. **Performance**: Are there optimization opportunities?
4. **Security**: Are inputs validated? Secrets protected?
5. **Maintainability**: Is the code readable and documented?

### Approval Workflow
```
Developer → PR Creation → Automated Checks → Peer Review → 
Technical Lead Review → Merge to develop → QA Verification
```

## Implementation Checklist
- [ ] Configure branch protection rules in repository
- [ ] Set up commit hooks for message validation
- [ ] Create issue templates for consistent tracking
- [ ] Configure automated changelog generation
- [ ] Document workflow in CONTRIBUTING.md
- [ ] Train team on conventions and tools