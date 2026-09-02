# Study Reader

Study Reader is a mobile-first, book-like web reader for Microsoft certification
study material. The first book targets DP-700, but the content contracts are
intended to support other Microsoft exams without application changes.

The application will combine FastAPI, Jinja, HTMX, authored Markdown, and a
Progressive Web App shell. Published chapters remain grounded in Microsoft
Learn, cite exact source pages, and present original explanations instead of
reproducing Microsoft Learn pages.

## Project status

The project is in its first reader milestone. The repository provides separate
public reader and private administration application factories, a validated
exam-agnostic book contract, the current DP-700 outline, sanitized Markdown
rendering, a responsive reader shell, automated boundary tests, and CI. Reader
preferences, local progress, annotations, and offline support remain roadmap
work.

## Architecture boundary

- `study_reader.reader` is the public, read-only application. It MUST NOT expose
  content refresh, publishing, mutation, or arbitrary URL-fetching endpoints.
- `study_reader.admin` is the private administration application. It MUST be
  reachable only through the owner's tailnet in deployment.
- Published content is a versioned, read-only input to the public process.
- Browser reading state remains local for the MVP.

## Local development

Prerequisites: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```shell
uv sync --group dev
uv run uvicorn study_reader.reader.app:create_app --factory --reload
```

The reader is then available at `http://127.0.0.1:8000`. To run the private
administration application on a separate port:

```shell
uv run uvicorn study_reader.admin.app:create_app --factory --port 8001
```

Run all local quality gates with:

```shell
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

Configuration uses environment variables beginning with `STUDY_READER_`. See
`.env.example` for non-secret examples. Never commit credentials or private
tailnet details.

## Microsoft attribution

Microsoft, Microsoft Fabric, Microsoft Learn, OneLake, and related names are
trademarks of the Microsoft group of companies. This independent open-source
project is not affiliated with or endorsed by Microsoft. Microsoft owns its
learning material; this project links to authoritative sources and publishes
original study-oriented writing under the repository license.

The DP-700 manifest records the official skills blueprint effective July 21,
2026. See [`docs/content-model.md`](docs/content-model.md) for stable identifier,
ordering, and source-mapping rules.

## Contributing and security

Work is tracked through GitHub issues and reviewed pull requests. Read
[`CONTRIBUTING.md`](CONTRIBUTING.md) before contributing. Please report
vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md).

## License

Copyright (c) 2026 Troy Scott. Source code and original project content are
available under the [MIT License](LICENSE), unless a file states otherwise.
