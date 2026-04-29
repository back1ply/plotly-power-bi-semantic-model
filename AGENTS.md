# AI Assistant Guidelines for plotly-power-bi-semantic-model

## Code Validation & Testing Requirements
**CRITICAL:** Python is a dynamically typed and evaluated language. Relying solely on `pytest` is insufficient when making structural or presentation-level changes, because callbacks or un-executed branches may hide undefined variables or import errors. 

Before proposing or finalizing ANY code changes, you MUST run the following tools in order to guarantee the integrity of the codebase:

1. **Static Type Checking (Pyright):**
   Run `pyright` to catch type inconsistencies, missing imports, and undefined variables across the entire AST.
   ```bash
   pyright
   ```

2. **Linting (Ruff):**
   Run `ruff check .` to catch syntax errors, unused imports, and style violations. Run `ruff format .` to format the code.
   ```bash
   ruff check .
   ruff format .
   ```

3. **Security Analysis (Bandit):**
   Run `bandit` to ensure no security vulnerabilities (like SQL injection or weak cryptography) were introduced.
   ```bash
   bandit -r . -c pyproject.toml
   ```

4. **Dead Code Detection (Vulture):**
   Run `vulture` to catch unused variables, functions, and imports left over from refactoring.
   ```bash
   vulture .
   ```

5. **Test Coverage (Pytest-Cov):**
   LLMs often write code without writing tests for it. You MUST run tests with coverage and ensure you do not drop the coverage percentage.
   ```bash
   pytest --cov=domain --cov=application --cov=infrastructure --cov=presentation
   ```

6. **Dependency Sync (Deptry):**
   Run `deptry` to ensure there are no missing, unused, or transitive dependencies in `pyproject.toml`.
   ```bash
   deptry .
   ```

7. **Exception Handling (Tryceratops):**
   Run `tryceratops` to analyze `try/except` blocks and prevent exception-handling anti-patterns.
   ```bash
   tryceratops .
   ```

8. **Docstring Coverage (Interrogate):**
   LLMs often write undocumented code. Run `interrogate` to ensure every new function, class, and module has a proper docstring explaining its purpose.
   ```bash
   interrogate -v .
   ```

9. **Dependency Vulnerabilities (Safety):**
   LLMs sometimes resolve dependency conflicts by downgrading a package to a vulnerable version. Run `safety` or `pip-audit` to ensure the project dependency tree remains secure.
   ```bash
   safety check
   ```

10. **End-to-End Browser Testing (Playwright / Dash Duo):**
    Unit tests do not catch client-side JavaScript crashes, CSS layout breaks, or React component failures in Dash. If you modify `layout.py`, `presentation/`, or `components/`, you MUST write and run E2E browser tests to verify the UI renders correctly.
    ```bash
    pytest tests/ -m e2e  # Or run specific UI test files
    ```

11. **Complexity & Magic Values Limit:**
    LLMs often write massive, deeply nested functions with hardcoded magic numbers. You MUST keep cyclomatic complexity low. If a function exceeds 10 branches, requires too many arguments, or uses undocumented magic numbers, you must refactor it into smaller, testable units before submitting.

12. **Mutation Testing (Mutmut):**
    LLMs sometimes write tests that execute code to get 100% coverage but forget to include meaningful assertions. Run `mutmut` to automatically insert bugs (mutations) into the code. If your tests still pass, they are weak and MUST be rewritten with stronger assertions.
    ```bash
    mutmut run
    ```

13. **Secret Scanning (Detect-Secrets):**
    LLMs sometimes mistakenly insert high-entropy strings, placeholder API keys, or SAS URIs into tests or code. Run `detect-secrets` to mathematically guarantee no credentials are leaked into the codebase.
    ```bash
    detect-secrets scan
    ```

14. **Architecture Boundary Enforcement (Pytest-Archon / Import-Linter):**
    LLMs frequently violate Clean Architecture by making an inner layer depend on an outer layer (e.g., `domain` importing from `infrastructure`). You MUST write tests using `pytest-archon` (or configure `import-linter`) to mathematically enforce that dependency arrows only point inward. If an import violates the architecture, the test must fail.
    ```bash
    pytest tests/test_architecture.py
    ```

15. **Source Code Spell Checking (Typos):**
    LLMs occasionally hallucinate variable names, make typos in user-facing strings, or misspell words in documentation. Run `typos` to instantly catch spelling errors across the entire codebase without false positives on code syntax.
    ```bash
    typos
    ```

16. **Visual Regression Testing (Playwright / Percy):**
    LLMs are terrible at CSS and layout styling. While E2E tests verify that buttons can be clicked, they do not verify if the chart is rendering off-screen or if the layout is broken. You MUST use visual regression testing (taking a screenshot and comparing it to a baseline) if you touch any CSS or Mantine UI components.
    ```bash
    pytest tests/ -m visual --update-snapshots
    ```

17. **Accessibility Testing (Axe-playwright-python):**
    LLMs almost never add `aria-` labels, `alt` text, or proper contrast ratios unless forced to. Run accessibility scans on the generated Dash UI to ensure the application remains usable for all users and complies with WCAG standards.
    ```bash
    just a11y
    ```

18. **Performance Profiling (Pytest-Benchmark / cProfile):**
    LLMs often write slow, non-vectorized `pandas` code (e.g., using `.apply()` or `iterrows()` instead of vectorized operations) or inefficient DAX queries. If you write data-processing logic, you MUST run benchmarks to prove your code operates in `O(1)` or `O(N)` time and doesn't introduce memory leaks.
    ```bash
    pytest tests/ --benchmark-only
    ```

19. **Property-Based Testing (Hypothesis):**
    LLMs usually only write "happy path" unit tests with one or two hardcoded examples. To truly prove your logic handles edge cases (like empty strings, NaNs, negative numbers, or massive payloads), you MUST use `hypothesis` to generate hundreds of randomized test cases.
    ```bash
    pytest tests/ --hypothesis-show-statistics
    ```

20. **Data Schema Validation (Pandera / Pydantic):**
    In data-heavy Dash applications, LLMs frequently make dangerous assumptions about the shape, types, and nullability of `pandas` DataFrames. You MUST use `pandera` (or `pydantic` for objects) to strictly validate the input and output schemas of your data transformation functions.

21. **Configuration & CI/CD Linting (Yamllint / Actionlint):**
    LLMs often break YAML indentation, TOML syntax, or GitHub Actions workflow files, which breaks the build pipeline silently. If you modify any `.yaml`, `.yml`, `.toml`, or `.json` files, you MUST run a structural linter to verify their syntax.
    ```bash
    yamllint .
    ```

22. **API Contract Testing (VCR.py / Schemathesis):**
    LLMs often manually mock external APIs in tests, making up fake responses that don't match reality. For apps communicating with external services (like the Power BI API), you MUST use `vcrpy` to record real API traffic or `schemathesis` to prove your code aligns with the actual API contract.

23. **Memory Leak Detection (Memray):**
    Dash apps use long-lived Python processes. LLMs frequently introduce memory leaks by caching data in global dictionaries without a TTL, or by appending to lists inside callbacks. You MUST profile long-running state with `memray` to prove your code does not steadily consume RAM over time.
    ```bash
    memray run -m pytest
    ```

24. **Advanced SAST (Semgrep):**
    LLMs can introduce subtle security vulnerabilities. Run `semgrep` to catch deep logical security flaws and framework-specific misconfigurations.
    ```bash
    just semgrep
    ```

25. **Load & Concurrency Testing (Locust):**
    Dash apps can fall over under concurrent load if callbacks are not properly memoized. You MUST run load tests using `locust` to simulate concurrent users.
    ```bash
    just load-test
    ```

26. **Maintainability Index (Xenon):**
    LLMs often write overly complex code. You MUST run `xenon` to ensure the codebase maintains an 'A' grade in cyclomatic complexity and maintainability.
    ```bash
    just maintainability
    ```

Alternatively, you MUST run `pre-commit run --all-files` if the project is a git repository, as this will run most of the above automatically.

**Do not claim a task is complete until all of these checks (`pyright`, `ruff`, `bandit`, `vulture`, `deptry`, `tryceratops`, `pytest --cov`, `interrogate`, `safety`, E2E UI checks, `mutmut`, `detect-secrets`, `pytest-archon`, `typos`, Visual, A11y, Performance, `hypothesis`, Schema Validation, Config Linting, API Contracts, Memory Leaks, Semgrep, Locust Load Tests, and Xenon) pass completely.**

## Operational Rules & Anti-Patterns
To prevent common AI-generated bugs, strictly adhere to these rules:

1. **Type Safety & Magic Bypasses:**
   - NEVER use `Any` as a crutch. Always define the exact type, `dataclass`, `TypedDict`, or `Protocol`.
   - NEVER suppress type errors with `# type: ignore`, `cast()`, or `noqa` comments unless explicitly instructed by the user. You must fix the underlying type mismatch.

2. **Error Handling & Logging:**
   - NEVER silently swallow exceptions (e.g., `except Exception: pass`).
   - All errors caught in the Infrastructure layer must be logged using `logger.exception("...")` and then wrapped in a Domain exception (e.g., `raise QueryError(...) from exc`).

3. **Surgical Changes Only:**
   - NEVER refactor, "clean up", or reformat code in files unrelated to the direct task at hand. Keep your blast radius small and changes surgical.
   - If you see a potential improvement in another module, mention it in the chat but do not modify the code unless the user approves.

4. **Secrets & Environment:**
   - NEVER hardcode passwords, API keys, client secrets, or sensitive URLs in the codebase.
   - Always route configuration through the `config.py` and environment variables.

5. **Dash Framework Rules (CRITICAL):**
   - **No Global State Mutation:** Dash is a multi-user web framework. NEVER mutate global variables (like lists, dicts, or DataFrames) inside a callback. This causes cross-user data leaks. Use `dcc.Store` for user-specific state.
   - **Duplicate Outputs:** Dash does not allow multiple callbacks to target the same `Output` unless you explicitly set `allow_duplicate=True` and `prevent_initial_call=True`.
   - **File Paths:** Never use raw relative paths (e.g., `open("assets/style.css")`). Always resolve paths relative to the current file using `Path(__file__).parent`.

6. **Dependencies:**
   - Do NOT run arbitrary `pip install` commands. If a new dependency is required, add it to `pyproject.toml` under `dependencies` or `dev` dependencies and explain why it is needed.

## Architecture Notes
- The project follows a strict Clean Architecture pattern.
- **Domain Layer:** Contains core entities (`domain/entities.py`) and interfaces/ports (`domain/ports.py`). Cannot depend on anything outside the domain.
- **Application Layer:** Orchestration and use cases. Can depend on Domain, but not Infrastructure.
- **Infrastructure Layer:** Implementations of ports (e.g., Power BI client, caches, repositories). 
- **Presentation Layer:** UI, Dash callbacks, charts, and styling. Should use specific domain ports via dependency injection (e.g., `get_repository(DataPort)`).
- **No Magic Strings:** Always use Python `Enums`, `Literal` types, or `dataclasses` for UI flags and configurations (e.g., `Orientation`, `SortOrder`, `ThemeColor`).

### Established Patterns

- **Nav routes — single source of truth:** Route strings live in `presentation/constants.py` (`ROUTE_HOME`, `ROUTE_SCHEMA`, `ROUTE_MODEL`, `ROUTE_DAX`, `NAV_ROUTES`). Do NOT hardcode route strings in `components/base.py` or anywhere else.

- **Pure function extraction for testability:** Dash callback inner functions (nested inside `register_callbacks`) are not directly testable. Any non-trivial logic must be extracted as a module-level pure function (see `compute_active_nav`, `handle_inspector_logic`, `validate_dax_query`). The inner callback delegates to it: `return pure_function(args)`.

- **DAX input hardening — domain layer:** User-supplied DAX strings must be validated via `domain.validate_dax_query(dax)` before reaching `PbiClient.query()`. Validation lives in `domain/utils.py` because it encodes domain rules (valid query structure), not presentation logic.

- **White-label theming — `ThemeConfig` in `config.py`:** App title, primary color, and font are parameterized via the `ThemeConfig` frozen dataclass, env-var driven. `layout.py` consumes it and passes values to `MantineProvider` and `build_sidebar`. Do not hardcode brand strings or Mantine color names anywhere else.

- **`components` may import from `presentation`:** Arch tests (`tests/test_architecture.py`) only restrict domain/application/infrastructure from importing presentation — `components` is part of the presentation tier and importing from `presentation.constants` is valid.