# Git Workflow for JobPulse

## Commit Message Format

```
feat: add new feature
fix: fix a bug
docs: update documentation
test: add or update tests
refactor: refactor code without changing behavior
chore: update dependencies, configuration
```

## Development Branch Naming

```
feat/feature-name
fix/bug-name
docs/what-to-document
```

## Making Changes

1. Create feature branch
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make changes and test
   ```bash
   pytest
   ```

3. Commit with clear messages
   ```bash
   git commit -m "feat: add ingestion feature"
   ```

4. Push and create PR
   ```bash
   git push origin feat/my-feature
   ```

## Code Style

- Follow PEP 8 for Python
- Use type hints
- Document functions with docstrings
- Keep functions focused and testable
