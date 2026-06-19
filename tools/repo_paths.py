"""Self-locating path constants for progenitor-registry dev tools.

Replaces the former cross-repo ``devkit_context`` glue (progenitor-devkit, now
dissolved). Paths resolve relative to this repo; the sibling protocol repo
defaults to ``../progenitor-protocol`` but can be relocated via environment
variables.
"""
from __future__ import annotations

import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent            # progenitor-registry/tools
REGISTRY_DIR = SCRIPT_DIR.parent                        # progenitor-registry repo root
GIT_DIR = REGISTRY_DIR                                  # back-compat alias (this repo)
TRAE_DIR = REGISTRY_DIR.parent                          # workspace holding sibling repos
PROTOCOL_DIR = Path(os.environ.get("PROGENITOR_PROTOCOL_DIR", TRAE_DIR / "progenitor-protocol")).resolve()
REPORT_DIR = Path(os.environ.get("PROGENITOR_REPORT_DIR", REGISTRY_DIR / "reports")).resolve()
RUNTIME_DIR = Path(os.environ.get("PROGENITOR_RUNTIME_DIR", TRAE_DIR / ".runtime" / "progenitor")).resolve()

__all__ = ["SCRIPT_DIR", "GIT_DIR", "TRAE_DIR", "PROTOCOL_DIR", "REGISTRY_DIR", "REPORT_DIR", "RUNTIME_DIR"]
