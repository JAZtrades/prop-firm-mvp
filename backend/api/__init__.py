"""Aggregate API routers into a package namespace.

Each submodule defines a FastAPI router with its own endpoints.
"""
from . import auth, accounts, trades, metrics, payouts, admin  # noqa: F401
