"""fxcast: PEN/USD exchange rate forecasting pipeline."""

from importlib.metadata import version

# Single source of truth: the version lives in pyproject.toml and is read
# from the installed package metadata, so it can never drift.
__version__ = version("fxcast")
