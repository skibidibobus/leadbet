"""Feature 1: Monorepo Layout & Module Boundaries Tests.

Verifies monorepo directory layout, pure math isolation of quant-engine,
absence of circular dependencies across packages, contract package exports,
and consistency of Python packaging metadata.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _extract_pyproject_dependencies(content: str) -> list[str]:
    """Helper to extract dependency package names from pyproject.toml without external toml library."""
    match = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if not match:
        return []
    deps_block = match.group(1)
    deps = re.findall(r'"([^"]+)"', deps_block)
    return [re.split(r"[><=~]", d)[0].strip().lower() for d in deps]


def test_feat_01_monorepo_directory_structure() -> None:
    """Verifies existence of required monorepo packages and pnpm workspace configuration."""
    required_dirs = [
        REPO_ROOT / "apps" / "web",
        REPO_ROOT / "apps" / "api",
        REPO_ROOT / "packages" / "quant-engine",
        REPO_ROOT / "packages" / "bookmaker-adapters",
        REPO_ROOT / "packages" / "contracts",
    ]
    for d in required_dirs:
        assert d.exists(), f"Required directory {d.relative_to(REPO_ROOT)} is missing"
        assert d.is_dir(), f"Path {d.relative_to(REPO_ROOT)} is not a directory"

    workspace_file = REPO_ROOT / "pnpm-workspace.yaml"
    assert workspace_file.exists(), "pnpm-workspace.yaml is missing at repository root"
    content = workspace_file.read_text(encoding="utf-8")
    assert "apps/*" in content, "pnpm-workspace.yaml must include 'apps/*'"
    assert "packages/*" in content, "pnpm-workspace.yaml must include 'packages/*'"


def test_feat_01_quant_engine_pure_math_isolation() -> None:
    """Verifies that packages/quant-engine has zero network, HTTP, or database dependencies."""
    pyproject_path = REPO_ROOT / "packages" / "quant-engine" / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing in packages/quant-engine"

    content = pyproject_path.read_text(encoding="utf-8")
    dep_names = _extract_pyproject_dependencies(content)

    prohibited = {
        "httpx",
        "requests",
        "aiohttp",
        "urllib3",
        "asyncpg",
        "psycopg2",
        "sqlite3",
        "fastapi",
        "flask",
        "sqlalchemy",
    }
    violations = prohibited.intersection(dep_names)
    assert not violations, f"quant-engine has prohibited network/DB dependencies: {violations}"

    # Also scan python files in quant_engine for network/DB imports
    quant_engine_src = REPO_ROOT / "packages" / "quant-engine" / "quant_engine"
    for py_file in quant_engine_src.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    assert (
                        root_mod not in prohibited
                    ), f"Prohibited import {root_mod} found in {py_file.relative_to(REPO_ROOT)}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    assert (
                        root_mod not in prohibited
                    ), f"Prohibited import from {root_mod} in {py_file.relative_to(REPO_ROOT)}"


def test_feat_01_circular_dependency_analysis() -> None:
    """Verifies that internal package dependencies form an acyclic directed graph (DAG)."""
    modules = {
        "quant_engine": REPO_ROOT / "packages" / "quant-engine" / "quant_engine",
        "bookmaker_adapters": REPO_ROOT / "packages" / "bookmaker-adapters" / "bookmaker_adapters",
        "api_src": REPO_ROOT / "apps" / "api" / "src",
    }

    # Verify quant_engine does not import bookmaker_adapters or api
    for py_file in modules["quant_engine"].rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("bookmaker_adapters")
                    assert not alias.name.startswith("apps")
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("bookmaker_adapters")
                assert not node.module.startswith("apps")

    # Verify bookmaker_adapters does not import apps
    for py_file in modules["bookmaker_adapters"].rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("apps")
                    assert not alias.name.startswith("api")
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("apps")
                assert not node.module.startswith("api")


def test_feat_01_contracts_package_exports_and_boundaries() -> None:
    """Verifies @quantkupon/contracts exports TypeScript types and schema without UI leakage."""
    pkg_json_path = REPO_ROOT / "packages" / "contracts" / "package.json"
    assert pkg_json_path.exists()

    with open(pkg_json_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    assert pkg.get("name") == "@quantkupon/contracts"
    assert "exports" in pkg
    assert "./types" in pkg["exports"]
    assert "./openapi.yaml" in pkg["exports"]
    assert "./schema.sql" in pkg["exports"]

    # Prohibited frontend dependencies in contracts
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    prohibited_ui = {"react", "react-dom", "next", "tailwindcss"}
    assert not prohibited_ui.intersection(deps.keys()), "Contracts package contains UI dependencies"


def test_feat_01_python_packaging_metadata_consistency() -> None:
    """Verifies that all Python modules define valid setuptools configuration and >=3.9 requirement."""
    pyproject_files = [
        REPO_ROOT / "packages" / "quant-engine" / "pyproject.toml",
        REPO_ROOT / "packages" / "bookmaker-adapters" / "pyproject.toml",
        REPO_ROOT / "apps" / "api" / "pyproject.toml",
    ]
    for p in pyproject_files:
        assert p.exists(), f"{p.relative_to(REPO_ROOT)} is missing"
        text = p.read_text(encoding="utf-8")
        assert "[build-system]" in text
        assert "[project]" in text
        assert 'requires-python = ">=3.9"' in text
        assert 'version = "0.1.0"' in text
