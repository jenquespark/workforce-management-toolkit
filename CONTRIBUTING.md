# Contributing

The Workforce Management Toolkit is in early stage (v0.1.0). Contributions are welcome but the project does not yet have a formal governance structure.

## Development setup

```bash
git clone https://github.com/jenquespark/workforce-management-toolkit.git
cd workforce-management-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
pip install pytest
```

## Running tests

```bash
pytest -v
```

## Code quality

```bash
ruff check .
ruff format --check .
```

## Guidelines

- Keep the toolkit small and honest
- Do not fabricate capability behavior
- All provider adapters must call real upstream libraries
- New capabilities require both implementation and tests
- Use the GitHub noreply identity for commits: `jenquespark <255307185+jenquespark@users.noreply.github.com>`