# Licenses

Project constraint: **every dependency must have an OSI-approved license.**
Each entry below was verified against the license file in the project's official
repository (GitHub API `/repos/{owner}/{repo}/license` + reading the file when
GitHub could not classify it), not only against PyPI metadata.

- **Last verified:** 2026-11-22 (versions from `pipeline/uv.lock`)
- **Scope:** `R` = runtime (shipped with `fxcast`), `D` = dev only (not shipped),
  `N` = `notebooks` group (local exploration only, never shipped)

## Python — direct dependencies

| Package | Version | Scope | License | Official repo |
|---|---|---|---|---|
| typer | 0.29.2 | R | MIT | [fastapi/typer](https://github.com/fastapi/typer) |
| httpx | 0.28.1 | R | BSD-3-Clause | [encode/httpx](https://github.com/encode/httpx) |
| pandas | 3.1.1 | R | BSD-3-Clause | [pandas-dev/pandas](https://github.com/pandas-dev/pandas) |
| pyarrow | 26.0.1 | R | Apache-2.0 | [apache/arrow](https://github.com/apache/arrow) |
| tzdata | 2026.6 | R | Apache-2.0 | [python/tzdata](https://github.com/python/tzdata) |
| ruff | 0.17.6 | D | MIT | [astral-sh/ruff](https://github.com/astral-sh/ruff) |
| mypy | 2.4.1 | D | MIT | [python/mypy](https://github.com/python/mypy) |
| pytest | 9.2.0 | D | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| pre-commit | 4.7.0 | D | MIT | [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit) |
| pandas-stubs | 3.1.0.261029 | D | BSD-3-Clause | [pandas-dev/pandas-stubs](https://github.com/pandas-dev/pandas-stubs) |
| nbstripout | 0.9.2 | D | MIT | [kynan/nbstripout](https://github.com/kynan/nbstripout) |
| jupyterlab | 4.6.6 | N | BSD-3-Clause | [jupyterlab/jupyterlab](https://github.com/jupyterlab/jupyterlab) |

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
| anyio | 4.16.0 | httpx | MIT | [agronholm/anyio](https://github.com/agronholm/anyio) |
| httpcore | 1.0.9 | httpx | BSD-3-Clause | [encode/httpcore](https://github.com/encode/httpcore) |
| h11 | 0.16.0 | httpcore | MIT | [python-hyper/h11](https://github.com/python-hyper/h11) |
| idna | 3.20 | httpx | BSD-3-Clause | [kjd/idna](https://github.com/kjd/idna) |
| certifi | 2026.11.20 | httpx | MPL-2.0 ³ | [certifi/python-certifi](https://github.com/certifi/python-certifi) |
| numpy | 2.5.5 (2.4.6 on 3.11) | pandas, pyarrow | BSD-3-Clause ⁴ | [numpy/numpy](https://github.com/numpy/numpy) |
| python-dateutil | 4.0.0 | pandas | Apache-2.0 AND BSD-3-Clause ⁵ | [dateutil/dateutil](https://github.com/dateutil/dateutil) |
| nbformat | 5.11.1 | nbstripout | BSD-3-Clause | [jupyter/nbformat](https://github.com/jupyter/nbformat) |
| fastjsonschema | 2.22.3 | nbformat | BSD-3-Clause | [horejsek/python-fastjsonschema](https://github.com/horejsek/python-fastjsonschema) |
| jsonschema | 4.26.0 | nbformat | MIT | [python-jsonschema/jsonschema](https://github.com/python-jsonschema/jsonschema) |
| jsonschema-specifications | 2025.9.1 | jsonschema | MIT | [python-jsonschema/jsonschema-specifications](https://github.com/python-jsonschema/jsonschema-specifications) |
| referencing | 0.37.0 | jsonschema | MIT | [python-jsonschema/referencing](https://github.com/python-jsonschema/referencing) |
| rpds-py | 2026.9.1 | referencing | MIT | [crate-py/rpds](https://github.com/crate-py/rpds) |
| attrs | 26.1.0 | jsonschema | MIT | [python-attrs/attrs](https://github.com/python-attrs/attrs) |
| jupyter-core | 5.9.1 | nbformat | BSD-3-Clause | [jupyter/jupyter_core](https://github.com/jupyter/jupyter_core) |
| traitlets | 5.16.1 | nbformat | BSD-3-Clause | [ipython/traitlets](https://github.com/ipython/traitlets) |

¹ pathspec is being relicensed to `MIT OR MPL-2.0` (both files are in the repo; the
released package still declares MPL-2.0). MPL-2.0 is OSI-approved, file-level
copyleft; it is dev-only here and we do not modify it. No conflict with MIT.
² GitHub cannot auto-classify the file; its text is the 3-clause BSD license.
³ certifi's code is MPL-2.0; it bundles Mozilla's CA certificate list. OSI-approved,
file-level copyleft; used unmodified.
⁴ numpy's wheels bundle third-party components under 0BSD, MIT, Zlib and CC0-1.0
(declared in its `License-Expression`). CC0-1.0 is a public-domain dedication, not an
OSI license; it imposes no obligations and is accepted here as such.
⁵ PyPI metadata says BSD-3-Clause; the repo `LICENSE` says contributions since 2017
are Apache-2.0 and earlier ones BSD-3-Clause (both OSI).

## Python — `notebooks` group only (transitive of jupyterlab)

Exploration-only, never shipped in the package or the Docker image. **Verified from
installed package metadata** (`License-Expression` / trove classifiers), not repo by
repo: 71 packages would exceed the unauthenticated GitHub API rate limit, and the risk
is low because nothing here is distributed. All are OSI-approved.

| Package | Version | License (metadata) |
|---|---|---|
| appnope | 1.0.0 | BSD-2-Clause |
| argon2-cffi-bindings | 26.2.0 | MIT |
| argon2-cffi | 25.1.0 | MIT |
| arrow | 1.4.0 | Apache-2.0 |
| asttokens | 3.0.2 |  |
| async-lru | 2.4.0 | MIT |
| babel | 2.18.0 | BSD ⁷ |
| beautifulsoup4 | 4.15.0 | MIT |
| bleach | 6.4.0 |  |
| cffi | 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 |  |
| comm | 0.2.3 | BSD ⁷ |
| debugpy | 1.8.22 | MIT |
| defusedxml | 0.7.1 | PSF-2.0 |
| executing | 2.3.0 | MIT |
| fqdn | 1.6.0 | MPL-2.0 |
| ipykernel | 7.4.0 | BSD-3-Clause |
| ipython-pygments-lexers | 1.1.1 | BSD ⁷ |
| ipython | 9.18.1 | BSD-3-Clause |
| isoduration | 20.11.0 | ISC |
| jedi | 0.20.1 | MIT |
| jinja2 | 3.1.6 | BSD ⁷ |
| json5 | 0.17.3 | Apache-2.0 |
| jsonpointer | 3.12 | BSD-3-Clause |
| jupyter-builder | 1.3.0 | Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MIT |
| jupyter-client | 8.10.0 | BSD ⁷ |
| jupyter-events | 0.12.1 | BSD ⁷ |
| jupyter-lsp | 2.3.1 | BSD ⁷ |
| jupyter-server-terminals | 0.5.4 | BSD ⁷ |
| jupyter-server | 2.21.1 | BSD ⁷ |
| jupyterlab-pygments | 0.3.0 | BSD ⁷ |
| jupyterlab-server | 2.28.1 | BSD ⁷ |
| jupyterlab | 4.6.6 | BSD ⁷ |
| lark | 1.3.1 | MIT |
| markupsafe | 3.0.4 | BSD-3-Clause |
| matplotlib-inline | 0.2.2 | BSD-3-Clause |
| mistune | 3.4.0 | BSD ⁷ |
| nbclient | 0.11.0 | BSD ⁷ |
| nbconvert | 7.17.2 | BSD ⁷ |
| nest-asyncio2 | 1.7.4 | BSD ⁷ |
| notebook-shim | 0.2.4 | BSD ⁷ |
| overrides | 7.7.0 | Apache-2.0 ⁶ |
| pandocfilters | 1.5.1 | BSD ⁷ |
| parso | 0.8.7 | MIT |
| pexpect | 4.9.0 | ISC |
| prometheus-client | 0.26.0 | Apache-2.0 AND BSD-2-Clause |
| prompt-toolkit | 3.0.53 | BSD ⁷ |
| psutil | 7.2.2 |  |
| ptyprocess | 0.7.0 | ISC |
| pure-eval | 0.2.4 | MIT |
| pycparser | 3.12 | BSD-3-Clause |
| python-json-logger | 4.2.0 | BSD-2-Clause |
| pywinpty | 3.1.2 | MIT ⁶ |
| pyzmq | 27.3.0 | BSD-3-Clause |
| requests | 2.34.2 | Apache-2.0 |
| rfc3339-validator | 0.1.4 | MIT |
| rfc3986-validator | 0.1.1 | MIT |
| rfc3987-syntax | 1.1.0 | MIT |
| send2trash | 2.2.0 | BSD-3-Clause |
| six | 1.17.0 | MIT |
| soupsieve | 2.10 | MIT |
| stack-data | 0.6.3 | MIT |
| terminado | 0.18.1 | BSD ⁷ |
| tinycss2 | 1.5.1 | BSD ⁷ |
| tornado | 6.6.1 | Apache-2.0 |
| uri-template | 1.3.0 | MIT |
| urllib3 | 2.8.0 | MIT |
| wcwidth | 0.9.5 | MIT |
| webcolors | 25.10.0 | BSD ⁷ |
| webencodings | 0.6.1 | BSD ⁷ |
| websocket-client | 1.9.2 |  |

⁶ Platform-specific, not installed on macOS; license verified in its repo.
⁷ Metadata only says "BSD License" without the variant; all are OSI-approved BSD variants.

## Tooling (not Python dependencies)

| Tool | Use | License | Official repo |
|---|---|---|---|
| uv | Package/env/Python manager, build backend (`uv_build`) | MIT OR Apache-2.0 | [astral-sh/uv](https://github.com/astral-sh/uv) |
| pre-commit-hooks | Generic hooks in `.pre-commit-config.yaml` | MIT | [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) |

## How to update this file

1. List the locked set per group: `uv export --project pipeline --no-dev` (runtime),
   `--only-dev`, and `--no-default-groups --group notebooks` (add `--no-hashes --no-emit-project`).
2. For each new package, open its official repo and read the `LICENSE` file
   (PyPI metadata can be stale or missing — see pathspec above).
3. Reject anything that is not OSI-approved, and for pretrained models also check
   the license of the **weights**, not only the code.
