# Contributing to Study Reader

Thank you for helping make certification study material easier to read.

## Workflow

1. Choose or open a GitHub issue before substantial work.
2. Discuss changes that alter scope, architecture, security boundaries, or
   content policy before implementation.
3. Create a focused branch and include tests or content checks with the change.
4. Open a pull request that links the issue and explains verification evidence.
5. Wait for human approval before merging.

Pull requests SHOULD be small enough to review carefully. New behavior MUST be
covered by representative tests. A discovered failure SHOULD become a named
regression test before it is fixed.

## Content contributions

Study chapters MUST be original writing grounded in authoritative sources.
They MUST identify source URLs and MUST NOT copy Microsoft Learn pages wholesale.
Claims about current exam objectives or Microsoft Fabric behavior MUST be
checked against current official Microsoft documentation.

## Local checks

```shell
uv sync --group dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

Do not commit secrets, private network details, generated caches, local browser
state, or unpublished review artifacts.
