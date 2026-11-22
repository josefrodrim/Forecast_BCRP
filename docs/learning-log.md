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

---

## Fase 1 — Ingesta

### 1.1 Grupo `notebooks` y nbstripout — 2026-11-22

**Qué hicimos:** `httpx` y `pandas` como dependencias runtime; grupo `notebooks` (jupyterlab);
`nbstripout --keep-output` como hook de pre-commit; `notebooks/01_api.ipynb` inicial.

**Comandos:**
```bash
uv add --project pipeline pandas httpx
uv add --project pipeline --group notebooks jupyterlab
uv run --project pipeline --group notebooks jupyter lab notebooks/01_api.ipynb
```

**Conceptos:**
- El kernel corre en el mismo `.venv` del pipeline → el notebook importa exactamente lo que usa el paquete.
- Grupos opt-in: `notebooks` no se instala por defecto (CI y Docker más livianos).
- `--keep-output`: se ven tablas/gráficos en GitHub; se limpia `execution_count` y metadata.
- pandas 3.x: Copy-on-Write siempre activo; dtype `str` por defecto; *chained assignment* ya no modifica.

**Errores / observaciones:**
- nbstripout normalizó el notebook escrito a mano (renumeró ids de celda) → `Failed` + re-`git add`.
- `[WARNING] Unstaged files detected`: Jupyter guardó el notebook después del `git add`. pre-commit
  guarda esos cambios en un stash, corre los hooks solo sobre lo que está en staging y los restaura.
- Warnings de Jupyter: `not trusted` (no ejecuta JS de outputs ajenos), `TCP without encryption`
  (solo escucha en localhost).

### 1.2 Primera petición y anatomía del JSON — 2026-11-22

**Conceptos:**
- Respuesta HTTP = status + headers + body. `200` ≠ "datos correctos".
- Timeout explícito siempre (httpx usa 5 s por defecto).
- Rango de fechas fijo en el notebook → outputs reproducibles.

**Hallazgos:**
- `Content-Type: text/html` aunque el body es JSON. httpx `.json()` ignora el header.
- `x-cdn: Imperva` (WAF anti-bots): sus páginas de bloqueo también llegan como `200 text/html`
  → ni status ni header distinguen datos de bloqueo. Riesgo con IPs de datacenter (GitHub Actions).
- Valores como strings; 15 periodos hábiles entre 2 y 20 nov 2026.

### 1.3 Parseo de fechas y valores — 2026-11-22

**Conceptos:**
- `%y` sigue la regla POSIX: `68 → 2068`, `69 → 1969` (99 años de distancia por un día).
  El pipeline se rompería el 1-ene-2069 sin error visible.
- `%b` depende del locale (`LC_TIME`).
- Fallar fuerte vs en silencio: `pd.to_numeric(errors="coerce")` convierte `"3,41"` en NaN
  sin avisar; el parser explícito lanza `ValueError`.
- Guardar precisión completa (~14 decimales). `"dec": "3"` es solo para mostrar; redondear
  sesga retornos y volatilidad.

### 1.4 Casos borde de la API — 2026-11-22

**Concepto:** explorar una API por experimentación, con `sleep` entre llamadas (cortesía + WAF).

**Hallazgos:**
- Código inválido → `200` + HTML de 155 B (challenge de Imperva). Una llamada válida justo
  después devolvió la misma página → el mismo HTML puede ser permanente o transitorio.
- La API devuelve la grilla L–V del rango pedido: feriados **y fechas futuras/no publicadas** como `n.d.`.
  Último dato real: jueves 19 nov; viernes 20 = `n.d.` el domingo 22 → rezago > 1 día hábil.
- Septiembre llega como `"Set"` aunque la URL pide `/ing` → `%b` falla.
- Sin rango máximo: 1997–2026, 2 series, 7798 periodos en una llamada de ~0.5 s.
- `values` es posicional respecto a `config.series`.
- Compra y venta son `n.d.` los mismos 355 días (≈ 12 feriados/año × 30 años).
- Primer dato real: `02.Jan.97`; antes, grilla `n.d.`.

### 1.5 Key takeaways del notebook 01 — 2026-11-22

**Reglas de diseño para `src/`:**
- `parse_date`: mapeo propio de meses `{Jan..Dec, Set, Sep}`; siglo resuelto dentro de `[start, end]`.
- `parse_value`: `"n.d." → NaN`; `float()`; cualquier otra cosa → error.
- Respuesta no-JSON → error transitorio (reintentar); JSON con forma inesperada → permanente (fallar).
- Recortar los `n.d.` iniciales y finales; conservar como NaN los interiores (feriados).
- Ingesta incremental: volver a pedir los últimos 10 días hábiles + upsert por fecha (idempotente).
- Backfill en un solo request.

### 1.6 Parser puro `ingest/parse.py` — 2026-11-22

**Qué hicimos:** `parse_date`, `parse_value`, `parse_response` y `BCRPParseError`; `pandas-stubs`.

**Conceptos:**
- *Functional core, imperative shell*: la lógica sin I/O se testea con fixtures, sin red.
- `payload: object` en vez de `dict[str, Any]`: mypy strict obliga a validar con `isinstance`.
- `float("nan")` y `float("inf")` son válidos en Python → rechazarlos explícitamente.
- `raise ... from exc` encadena excepciones y conserva la causa raíz.

**Errores:**
- `cd: no such file or directory: pipeline`: la shell ya estaba dentro de `pipeline/`
  (un `cd` previo cambió el directorio de trabajo de la sesión). Tip: `pwd` antes de usar rutas relativas.

### 1.7 Tests con fixtures grabadas — 2026-11-22

**Qué hicimos:** `scripts/record_fixtures.py` (6 casos reales + `manifest.json`), fixture
factory en `conftest.py`, 37 tests parametrizados.

**Conceptos:**
- Fixtures **grabadas** > inventadas: capturan rarezas reales (`Set`, `text/html`, `n.d.`).
- `pytest.mark.parametrize`: un test, muchos casos, cada uno con su id.
- Los casos de "contrato roto" mutan una copia (`deepcopy`) de una fixture real.

**Hallazgos / errores:**
- La página del código inválido es un challenge de Imperva Incapsula (`/_Incapsula_Resource`)
  y su tamaño varía (155 B → 287 B) → no detectar bloqueos por tamaño.
- `end-of-file-fixer` habría agregado `\n` a las fixtures → `exclude: ^pipeline/tests/fixtures/`
  solo en los dos fixers.
- Ejercicio: comentar `"Set": 9` → 2 tests fallan, uno con la fixture real (el bug de cada septiembre).

### 1.8 Cliente HTTP con reintentos — 2026-11-22

**Qué hicimos:** `BCRPClient`, `RetryPolicy`, `backoff_delay` (full jitter), taxonomía de
errores; 17 tests con `httpx.MockTransport`.

**Conceptos:**
- GET es idempotente → seguro de reintentar.
- Backoff exponencial + *full jitter* evita el *thundering herd*.
- Inyección de dependencias (`http`, `sleep`, `rng`) → tests sin red y sin esperas.
- `httpx.TimeoutException` es subclase de `TransportError` → capturarla primero.
- El parseo va fuera del loop de reintentos: un error permanente no se reintenta.

**Errores:**
- Jupyter abierto con una versión vieja en memoria sobrescribió `01_api.ipynb` (perdió la celda
  de Key takeaways). Solución: cerrar Jupyter y `git checkout -- notebooks/01_api.ipynb`.
  Lección: no editar el mismo notebook desde dos lugares → en `02_eda` el usuario pega las celdas.

### 1.9 Storage Parquet con upsert idempotente — 2026-11-22

**Qué hicimos:** `ingest/series.py` (`buy`/`sell`), `storage/` con `Storage` (Protocol),
`UpsertResult`, `ParquetStorage`; 16 tests.

**Conceptos:**
- `Protocol` = tipado estructural (no hace falta herencia).
- Idempotencia: el segundo upsert no cambia nada y **no reescribe el archivo** → sin diff en git.
- Escritura atómica: archivo temporal en el mismo directorio + `os.replace`.
- "Gana el dato entrante" (revisiones del BCRP); `NaN == NaN` cuenta como sin cambio.
- `date` como Arrow `date32`.

**Errores:**
- mypy: `"Index[Any]" has no attribute "as_unit"` → los stubs pierden `DatetimeIndex` tras
  `astype` / `sort_index`; se envuelve con `pd.DatetimeIndex(...)`.
- Commit con el mensaje del paso anterior (flecha ↑ del historial) →
  `git commit --amend -m "..."` **antes** del push. Nunca hacer amend de commits ya subidos.
  En un amend que solo cambia el mensaje los hooks salen `Skipped` (no hay nada en staging).

### 1.10 CLI `fxcast ingest` y backfill — 2026-11-22

**Qué hicimos:** `ingest/service.py` (`resolve_window`, `run_ingest`, `today_lima`), comando
`ingest` (`--backfill`, `--start`, `--end`, `--data-dir` / `FXCAST_DATA_DIR`), `tzdata`.
Backfill real: 7796 filas 1997-01-02 → 2026-11-19 en `data/rates.parquet` (~107 KB).

**Comandos:**
```bash
uv run --project pipeline fxcast ingest --backfill   # updated: inserted=7796 ...
uv run --project pipeline fxcast ingest              # no-op: ... unchanged=11
uv run --project pipeline fxcast ingest --data-dir /tmp/empty; echo "exit=$?"   # exit=1
```

**Conceptos:**
- Contrato del CLI: stdout = resultado; stderr = logs/errores; exit 0 (también el no-op),
  1 (error del pipeline), 2 (uso incorrecto).
- El reloj es una dependencia: "hoy" en hora de Lima, inyectado en los tests.
- Solo los errores conocidos se resumen en una línea; los inesperados conservan su traceback.
- Commits separados para código y datos (`feat(cli)` / `chore(data)`).
- pre-commit trata el Parquet como binario (solo corre `check-added-large-files`); git muestra
  `0 insertions` porque no hay líneas.

### 1.11 Cierre de la Fase 1 — 2026-11-22

**Qué hicimos:** 4 tests `integration` contra la API real (opt-in con `-m integration`),
ADR-0002 (ingesta) y ADR-0003 (storage), `licenses.md` actualizado.

**Comandos:**
```bash
uv run --project pipeline pytest -q                  # 84 passed, 4 deselected
uv run --project pipeline pytest -q -m integration   # 4 passed (red real)
```

**Conceptos:**
- Pirámide de tests: muchos unitarios rápidos y deterministas; pocos de integración que
  verifican que los supuestos siguen vigentes.
- `addopts` con `-m 'not integration'`: un `-m` posterior en la línea de comandos lo reemplaza.
- Licencias: runtime y dev verificadas en el repo oficial; las 71 transitivas del grupo
  `notebooks` por metadata (límite de la API de GitHub: 60 peticiones por hora sin autenticar).
- Hallazgos: python-dateutil es Apache-2.0 + BSD-3 (PyPI solo dice BSD); certifi es MPL-2.0;
  numpy incluye componentes CC0-1.0.
