# NoxRunner Documentation

This directory contains the Sphinx documentation source for NoxRunner.

## Building Documentation

### Using Make

```bash
cd docs
make html
```

### Using Sphinx Directly

```bash
cd docs
sphinx-build -M html source build
```

## Documentation Structure

- `source/`: Sphinx source files
  - `index.rst`: Main documentation index
  - `introduction.rst`: Introduction and overview
  - `quickstart.rst`: Quick start guide
  - `api_reference/`: API documentation
  - `user_guide/`: User guides
  - `tutorial/`: Step-by-step tutorials
  - `examples/`: Code examples

## Requirements

Documentation dependencies are installed with:

```bash
pip install -e ".[docs]"
```

Or using uv:

```bash
uv sync --group docs
```

