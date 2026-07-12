"""
Scientific Logger
==================

Lightweight, pre-configured console logging helper for the Asterion
scientific engine.

Provides :func:`get_logger` — the **single entry-point** every module
in the ``scientific`` package should use to obtain a logger.  This keeps
formatting, level configuration, and handler setup consistent across the
engine without pulling in heavy frameworks.

Design
-------
* **Console-only by default** — research/simulation workflows run in
  terminals and Jupyter notebooks; file-based sinks can be added later
  via the standard ``logging`` API without changing call sites.
* **Structured prefix** — every log line includes the ISO timestamp,
  severity, and fully-qualified logger name so that interleaved output
  from parallel simulations remains traceable.
* **No global side-effects** — :func:`get_logger` only attaches a handler
  to the specific logger requested (or the ``scientific`` root logger).
  It does **not** call ``logging.basicConfig()`` which would hijack the
  application-level configuration.
* **Idempotent** — calling :func:`get_logger` multiple times with the
  same name returns the same logger instance and does not add duplicate
  handlers.

Usage::

    >>> from scientific.logger import get_logger
    >>> log = get_logger(__name__)
    >>> log.info("Simulation started with %d towers", 4)
    2026-07-10 10:30:00 | INFO     | scientific.simulation.runner | Simulation started with 4 towers

    >>> from scientific.logger import get_logger
    >>> log = get_logger("scientific.validation")
    >>> log.warning("RSSI value %.1f dBm is unusually strong", -25.0)
    2026-07-10 10:30:01 | WARNING  | scientific.validation | RSSI value -25.0 dBm is unusually strong
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Root logger name for the entire scientific package.
ROOT_LOGGER_NAME: str = "scientific"

#: Default log format — ISO timestamp | severity (padded) | logger name | message.
DEFAULT_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

#: Default date format (ISO 8601 without microseconds).
DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

#: Environment variable that overrides the default log level.
LOG_LEVEL_ENV_VAR: str = "ASTERION_LOG_LEVEL"

#: Fallback level when neither the env-var nor an explicit level is given.
FALLBACK_LEVEL: int = logging.INFO


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_level(level: Optional[str | int] = None) -> int:
    """Resolve the effective log level.

    Priority order:
        1. Explicit *level* argument.
        2. ``ASTERION_LOG_LEVEL`` environment variable.
        3. :data:`FALLBACK_LEVEL` (``INFO``).

    Args:
        level: A logging level name (``"DEBUG"``, ``"WARNING"``, …) or
            numeric constant.  Case-insensitive for strings.

    Returns:
        A numeric logging level.
    """
    if level is not None:
        if isinstance(level, int):
            return level
        resolved = logging.getLevelName(level.upper())
        if isinstance(resolved, int):
            return resolved
        # getLevelName returns "Level <X>" for unknown names in older Python
        return FALLBACK_LEVEL

    env_val = os.environ.get(LOG_LEVEL_ENV_VAR)
    if env_val is not None:
        resolved = logging.getLevelName(env_val.upper())
        if isinstance(resolved, int):
            return resolved

    return FALLBACK_LEVEL


def _make_console_handler(
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
) -> logging.StreamHandler:
    """Create a ``stderr``-bound :class:`logging.StreamHandler`.

    Args:
        fmt: Log message format string.
        datefmt: Date/time format string.

    Returns:
        A configured :class:`logging.StreamHandler`.
    """
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    return handler


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_logger(
    name: Optional[str] = None,
    *,
    level: Optional[str | int] = None,
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    """Return a configured :class:`logging.Logger` for the scientific engine.

    If *name* is ``None``, the root ``"scientific"`` logger is returned.
    A console handler is attached **only** if the logger has no handlers
    yet, so calling this function multiple times is safe.

    Args:
        name: Logger name.  Typically ``__name__`` of the calling module.
            If the name does not start with ``"scientific"``, it is used
            as-is (useful for tests or external consumers).
        level: Override the log level for this logger.  See
            :func:`_resolve_level` for resolution order.
        fmt: Format string for log messages.
        datefmt: Date/time format string.

    Returns:
        A ready-to-use :class:`logging.Logger`.

    Example::

        >>> log = get_logger(__name__)
        >>> log.debug("Running multilateration with seed=%d", 42)
    """
    logger_name = name or ROOT_LOGGER_NAME
    logger = logging.getLogger(logger_name)

    # Resolve level
    effective_level = _resolve_level(level)
    logger.setLevel(effective_level)

    # Attach a console handler if none exist (idempotent guard)
    if not logger.handlers:
        logger.addHandler(_make_console_handler(fmt=fmt, datefmt=datefmt))

    # Prevent propagation to the root logger to avoid duplicate output
    # when the application also configures logging.
    logger.propagate = False

    return logger


def set_level(level: str | int, name: Optional[str] = None) -> None:
    """Change the log level for an existing scientific logger at runtime.

    Useful for temporarily enabling ``DEBUG`` output during an
    interactive debugging session.

    Args:
        level: New logging level (name or numeric constant).
        name: Logger name.  Defaults to the root ``"scientific"`` logger.
    """
    logger = logging.getLogger(name or ROOT_LOGGER_NAME)
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
    logger.setLevel(level)


def silence(name: Optional[str] = None) -> None:
    """Suppress all output from a scientific logger.

    Equivalent to ``set_level(logging.CRITICAL + 1, name)``.

    Args:
        name: Logger name.  Defaults to the root ``"scientific"`` logger.
    """
    set_level(logging.CRITICAL + 1, name)
