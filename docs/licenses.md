# Licenses

Project constraint: **every dependency must have an OSI-approved license.**
Each entry below was verified against the license file in the project's official
repository (GitHub API `/repos/{owner}/{repo}/license` + reading the file when
GitHub could not classify it), not only against PyPI metadata.

- **Last verified:** 2026-11-22 (versions from `pipeline/uv.lock`)
- **Scope:** `R` = runtime (shipped with `fxcast`), `D` = dev only (not shipped)

## Python — direct dependencies

| Package | Version | Scope | License | Official repo |
|---|---|---|---|---|
| typer | 0.29.2 | R | MIT | [fastapi/typer](https://github.com/fastapi/typer) |
| ruff | 0.17.6 | D | MIT | [astral-sh/ruff](https://github.com/astral-sh/ruff) |
| mypy | 2.4.1 | D | MIT | [python/mypy](https://github.com/python/mypy) |
| pytest | 9.2.0 | D | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| pre-commit | 4.7.0 | D | MIT | [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit) |

## Python — transitive dependencies

| Package | Version | Pulled by | License | Official repo |
|---|---|---|---|---|
| rich | 15.0.0 | typer | MIT | [Textualize/rich](https://github.com/Textualize/rich) |
| shellingham | 1.5.4 | typer | ISC | [sarugaku/shellingham](https://github.com/sarugaku/shellingham) |
| typing-extensions | 4.16.0 | typer, mypy | PSF-2.0 | [python/typing_extensions](https://github.com/python/typing_extensions) |
| markdown-it-py | 4.3.0 | rich | MIT | [executablebooks/markdown-it-py](https://github.com/executablebooks/markdown-it-py) |
| mdurl | 0.1.2 | markdown-it-py | MIT | [executablebooks/mdurl](https://github.com/executablebooks/mdurl) |
| pygments | 2.21.0 | rich, pytest | BSD-2-Clause | [pygments/pygments](https://github.com/pygments/pygments) |
| annotated-doc | 0.0.7 | typer | MIT | [fastapi/annotated-doc](https://github.com/fastapi/annotated-doc) |
| pydantic | 2.14.4 | typer | MIT | [pydantic/pydantic](https://github.com/pydantic/pydantic) |
| pydantic-core | 2.50.5 | pydantic | MIT | [pydantic/pydantic-core](https://github.com/pydantic/pydantic-core) |
| typing-inspection | 0.4.5 | pydantic | MIT | [pydantic/typing-inspection](https://github.com/pydantic/typing-inspection) |
| annotated-types | 0.8.0 | pydantic | MIT | [annotated-types/annotated-types](https://github.com/annotated-types/annotated-types) |
| colorama | 0.4.6 | typer, pytest (Windows only) | BSD-3-Clause | [tartley/colorama](https://github.com/tartley/colorama) |
| mypy-extensions | 1.2.0 | mypy | MIT | [python/mypy_extensions](https://github.com/python/mypy_extensions) |
| librt | 0.17.0 | mypy | MIT | [mypyc/librt](https://github.com/mypyc/librt) |
| ast-serialize | 0.13.1 | mypy | MIT | [mypyc/ast_serialize](https://github.com/mypyc/ast_serialize) |
| pathspec | 1.1.1 | mypy | MPL-2.0 ¹ | [cpburnz/python-pathspec](https://github.com/cpburnz/python-pathspec) |
| pluggy | 1.7.0 | pytest | MIT | [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy) |
| iniconfig | 2.3.1 | pytest | MIT | [pytest-dev/iniconfig](https://github.com/pytest-dev/iniconfig) |
| packaging | 26.3 | pytest | Apache-2.0 OR BSD-2-Clause | [pypa/packaging](https://github.com/pypa/packaging) |
| cfgv | 3.5.0 | pre-commit | MIT | [asottile/cfgv](https://github.com/asottile/cfgv) |
| identify | 2.6.20 | pre-commit | MIT | [pre-commit/identify](https://github.com/pre-commit/identify) |
| nodeenv | 1.12.0 | pre-commit | BSD-3-Clause ² | [ekalinin/nodeenv](https://github.com/ekalinin/nodeenv) |
| virtualenv | 21.15.12 | pre-commit | MIT | [pypa/virtualenv](https://github.com/pypa/virtualenv) |
| distlib | 0.4.4 | virtualenv | PSF-2.0 | [pypa/distlib](https://github.com/pypa/distlib) |
| filelock | 4.3.0 | virtualenv | MIT | [tox-dev/filelock](https://github.com/tox-dev/filelock) |
| platformdirs | 4.14.8 | virtualenv | MIT | [tox-dev/platformdirs](https://github.com/tox-dev/platformdirs) |
| python-discovery | 1.9.6 | virtualenv | MIT | [tox-dev/python-discovery](https://github.com/tox-dev/python-discovery) |
| pyyaml | 6.0.4 | pre-commit | MIT | [yaml/pyyaml](https://github.com/yaml/pyyaml) |

¹ pathspec is being relicensed to `MIT OR MPL-2.0` (both files are in the repo; the
released package still declares MPL-2.0). MPL-2.0 is OSI-approved, file-level
copyleft; it is dev-only here and we do not modify it. No conflict with MIT.
² GitHub cannot auto-classify the file; its text is the 3-clause BSD license.

## Tooling (not Python dependencies)

| Tool | Use | License | Official repo |
|---|---|---|---|
| uv | Package/env/Python manager, build backend (`uv_build`) | MIT OR Apache-2.0 | [astral-sh/uv](https://github.com/astral-sh/uv) |
| pre-commit-hooks | Generic hooks in `.pre-commit-config.yaml` | MIT | [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) |

## How to update this file

1. List the locked set: `uv export --project pipeline --all-groups --no-hashes --no-emit-project`.
2. For each new package, open its official repo and read the `LICENSE` file
   (PyPI metadata can be stale or missing — see pathspec above).
3. Reject anything that is not OSI-approved, and for pretrained models also check
   the license of the **weights**, not only the code.
