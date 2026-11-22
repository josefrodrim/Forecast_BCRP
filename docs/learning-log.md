# Bitácora de aprendizaje

Registro paso a paso del proyecto: qué hicimos, comandos, conceptos, errores y cómo se resolvieron.

---

## Fase 0 — Setup

### 0.1 Inicializar el repositorio — 2026-11-22

**Qué hicimos:** `git init -b main`, `.gitignore` por secciones, `LICENSE` (MIT), `README.md` mínimo.
Repo remoto: `josefrodrim/Forecast_BCRP`.

**Comandos:**
```bash
git init -b main
git check-ignore -v .venv/ .env mlruns/   # ¿qué regla ignora cada ruta?
git add . && git commit -m "chore: initialize repository"
git remote add origin https://github.com/josefrodrim/Forecast_BCRP.git
git push -u origin main                   # -u: enlaza main con origin/main
```

**Conceptos:**
- `.gitignore` va **antes** del primer `git add`: sacar `.venv/` o `.env` del historial es caro.
- Una regla sin `/` inicial aplica a cualquier nivel; con `/` se ancla a la raíz.
- Conventional Commits: `tipo(scope): descripción` en imperativo. Tipos: `feat`, `fix`, `docs`,
  `build`, `ci`, `test`, `refactor`, `chore`. Permiten generar changelog y versionado semántico.
- `root-commit`: el primer commit, sin padre.

**Errores:**
- Bug evitado: `models/` en `.gitignore` habría ignorado también `pipeline/src/fxcast/models/`
  (código fuente) sin ningún aviso. Solución: `/models/`.
- Escribí `git log --oneline` como texto en vez de ejecutarlo en la shell. Hay que ejecutarlo
  como comando de terminal.

### 0.2 Estructura del monorepo — 2026-11-22

**Qué hicimos:** carpetas `pipeline/`, `notebooks/`, `web/`, `orchestration/airflow/`,
`lakehouse/`, `data/`, `docs/adr/`, `.github/`, cada una con un README corto.

**Conceptos:**
- Monorepo vs polyrepo: un cambio transversal (formato del JSON que exporta el pipeline y lee la
  web) va en un solo commit/PR. Costo: el CI debe filtrar por `paths:`.
- Git no versiona carpetas vacías, solo archivos → `.gitkeep` (convención) o README (documenta).
- `.github/` lleva `.gitkeep` y no README: GitHub muestra en la portada `.github/README.md` antes
  que el `README.md` de la raíz (prioridad: `.github/` > raíz > `docs/`).
- `git status -uall` lista archivos dentro de carpetas nuevas.

### 0.3 Paquete `fxcast` con uv — 2026-11-22

**Qué hicimos:** `pipeline/pyproject.toml` (PEP 621), `.python-version` (3.12), `uv.lock`,
src layout con `src/fxcast/__init__.py` y un CLI Typer con `fxcast --version`.

**Comandos:**
```bash
uv add typer                      # escribe la dependencia + actualiza uv.lock + instala
uv run fxcast --version           # fxcast 0.1.0
rm -rf .venv && uv sync           # reproducibilidad desde cero
uv tree --depth 1                 # árbol de dependencias
```

**Conceptos:**
- `pyproject.toml` reemplaza a `setup.py` / `requirements.txt`. `uv.lock` fija versiones exactas de
  todo el árbol → se commitea.
- `[build-system]` = backend que construye el wheel (`uv_build`).
- Entry point (`[project.scripts]`): instalar el paquete crea el comando `fxcast`.
- `[dependency-groups]` (PEP 735): dependencias de desarrollo que no viajan con el paquete.
- src layout: los tests importan el paquete **instalado**; los errores de empaquetado salen en local.
- `__version__` se lee de la metadata (`importlib.metadata`) → una sola fuente de verdad.
- `uv run` instala el proyecto en modo editable: cambios en `src/` se ven sin reinstalar.
- Dependencias se agregan cuando se necesitan, nunca "por si acaso".

**Errores:**
- `fatal: pathspec 'pipeline' did not match any files`: la shell estaba dentro de `pipeline/` y las
  rutas de git son relativas al cwd. Solución: `git add .` desde ahí (o volver a la raíz).

### 0.4 ruff, mypy y pytest — 2026-11-22

**Qué hicimos:** grupo `dev` con ruff, mypy y pytest; configuración en `pyproject.toml`
(`[tool.ruff]`, `[tool.mypy]` strict, `[tool.pytest.ini_options]`); smoke test con `CliRunner`.

**Comandos:**
```bash
uv add --dev ruff mypy pytest
uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest
uv run ruff check --fix           # arregla lo automático (no arregla bugs de tipos)
```

**Conceptos:**
- Linter (¿malos patrones?) ≠ formatter (¿estilo?) ≠ type checker (¿tipos encajan?) ≠ tests
  (¿hace lo correcto?). Análisis estático y tests son complementarios.
- mypy strict desde el inicio: endurecer después es más caro.
- `ignore_missing_imports` solo por módulo, nunca global (apagaría el chequeo en silencio).
- `--strict-markers` / `--strict-config`: los typos fallan en vez de ignorarse.
- Marker `integration` para tests contra la API real (excluidos en CI).
- El test compara con `__version__`, no con `"0.1.0"`, para no romperse al subir versión.
- Ejercicio: `a + "b"` con `a: int` pasa ruff pero mypy lo marca.

**Errores:**
- `tests/__init__.py` es necesario: sin él mypy nombra el módulo `test_cli` y el override
  `tests.*` no aplica.
- `warning: Failed to hardlink files`: el caché de uv y `.venv` están en filesystems distintos
  (disco externo). No es error. Silenciar con `export UV_LINK_MODE=copy` en `~/.zshrc`.

### 0.5 pre-commit — 2026-11-22

**Qué hicimos:** `.pre-commit-config.yaml` en la raíz con hooks genéricos
(`pre-commit-hooks` v6.0.0) + hooks `local` para `uv lock`, ruff format, ruff check y mypy.

**Comandos:**
```bash
uv add --project pipeline --dev pre-commit
uv run --project pipeline pre-commit autoupdate            # tags reales, no inventados
uv run --project pipeline pre-commit validate-config .pre-commit-config.yaml
uv run --project pipeline pre-commit run --all-files
uv run --project pipeline pre-commit install               # crea .git/hooks/pre-commit
git commit --no-verify                                     # solo emergencias
```

**Conceptos:**
- Git hooks viven en `.git/hooks/`, que no se versiona → el framework pre-commit versiona la
  configuración y `pre-commit install` crea el hook.
- Hooks `local` + `uv run`: las versiones de las herramientas salen solo de `uv.lock`
  (una fuente de verdad; hook, terminal y CI corren lo mismo).
- pre-commit solo revisa archivos **en staging**; `--all-files` revisa todo lo rastreado.
  Por eso `check yaml` salió `Skipped` con el YAML aún sin `git add`.
- pytest no va en pre-commit: el hook debe tardar segundos o la gente usa `--no-verify`.
- `check-added-large-files --maxkb=1000` protege `/data`, que se versiona.
- Si un hook modifica un archivo, el commit se aborta y hay que volver a `git add`.

**Errores / trampas:**
- `uv run --project pipeline mypy` desde la raíz **no encuentra** `[tool.mypy]`: mypy lee su
  config del cwd. Correría sin strict y pasaría en silencio. Solución: `--directory pipeline`.
- `astral-sh/uv-pre-commit` instala su propia copia de uv (otra versión) → reemplazado por un
  hook `local` con el uv del sistema.

### 0.6 Documentación viva — 2026-11-22

**Qué hicimos:** esta bitácora, plantilla de ADR, ADR-0001 (monorepo + uv + src layout) y
`docs/licenses.md` con las 33 dependencias bloqueadas (5 directas + 28 transitivas) y herramientas.

**Comandos:**
```bash
uv export --project pipeline --all-groups --no-hashes --no-emit-project   # set bloqueado
uv tree --package typer                                                  # quién trae qué
curl -s https://api.github.com/repos/{owner}/{repo}/license               # licencia según GitHub
```

**Conceptos:**
- ADR: registro corto de una decisión (contexto, opciones, decisión, consecuencias). Sirve para
  explicar el "por qué" meses después y en entrevistas.
- Verificar licencias en el repo oficial, no solo en PyPI:
  - GitHub devuelve `NOASSERTION` cuando no puede clasificar el archivo (mypy, packaging,
    distlib, nodeenv…) → hay que leer el `LICENSE`.
  - pathspec: PyPI dice MPL-2.0, GitHub detecta MIT; el repo está en relicenciamiento a
    `MIT OR MPL-2.0`. MPL-2.0 es OSI → aceptable (dev-only, no lo modificamos).
- typer 0.29 ya **no** depende de click (trae pydantic). No asumir árboles de memoria.
