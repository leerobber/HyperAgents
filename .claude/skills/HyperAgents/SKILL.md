```markdown
# HyperAgents Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the HyperAgents Python codebase. You'll learn how to structure files, write imports and exports, follow commit message conventions, and organize and run tests. This guide is ideal for contributors seeking to maintain consistency and quality in HyperAgents projects.

## Coding Conventions

### File Naming
- Use **snake_case** for all file and module names.
  - Example: `agent_utils.py`, `data_loader.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import parse_config
    from ..core.agent import Agent
    ```

### Export Style
- Use **named exports** (i.e., explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['Agent', 'parse_config']
    ```

### Commit Messages
- Use **conventional commit** format.
- Prefix new features with `feat`.
- Keep commit messages concise (average ~60 characters).
  - Example:
    ```
    feat: add support for multi-agent coordination
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new capability or module.
**Command:** `/add-feature`

1. Create a new Python file using snake_case naming.
2. Implement your feature, using relative imports for internal modules.
3. Define `__all__` for named exports if appropriate.
4. Write or update tests in a corresponding `*.test.*` file.
5. Commit changes with a message starting with `feat:`.
   - Example: `feat: implement agent negotiation protocol`
6. Submit a pull request for review.

### Writing and Running Tests
**Trigger:** When verifying new or existing functionality.
**Command:** `/run-tests`

1. Create or update test files matching the `*.test.*` pattern.
   - Example: `agent.test.py`
2. Write test cases for your feature or fix.
3. Use the project's preferred (currently unknown) testing framework.
4. Run tests to ensure all pass.
5. Address any failing tests before committing.

## Testing Patterns

- Test files are named using the pattern `*.test.*` (e.g., `module.test.py`).
- The specific testing framework is not detected; follow any existing patterns or consult maintainers.
- Place tests close to the code they verify, or in a dedicated `tests/` directory if present.

## Commands
| Command        | Purpose                                         |
|----------------|-------------------------------------------------|
| /add-feature   | Start the workflow for adding a new feature     |
| /run-tests     | Run the test suite for the codebase             |
```