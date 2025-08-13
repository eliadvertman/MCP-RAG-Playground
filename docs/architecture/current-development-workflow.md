# Current Development Workflow

### MVP Development Process

Following the **MVP Development Strategy** defined above, the current development workflow prioritizes:

**1. Story-Driven Development**
- All development follows BMad methodology with comprehensive stories
- Stories include detailed Dev Notes with architectural context
- Clear acceptance criteria and task breakdown for AI agents

**2. Quality Gates Without Overhead**
- **Code Standards**: SOLID principles enforced, clean interfaces maintained
- **Testing**: 80% coverage requirement with comprehensive markers
- **Architecture**: Modular design enables independent feature development
- **Simplicity**: Manual processes preferred over complex automation during MVP

**3. Current Development Setup**

```bash
pytest                    # All tests with coverage
pytest -m "unit"          # Fast unit tests only
pytest -m "not slow"      # Skip model downloads
pytest -m "integration"   # Full integration tests
```
