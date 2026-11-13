"""Feature 3: OpenAPI 3.1 Contract Validation & TypeScript Types.

Verifies OpenAPI 3.1.0 syntax, mandatory endpoint declarations,
$ref resolution integrity, TypeScript type generation completeness,
and JSON schema validation against fixtures.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict
import pytest
import yaml

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OPENAPI_PATH = REPO_ROOT / "packages" / "contracts" / "openapi.yaml"
TYPES_PATH = REPO_ROOT / "packages" / "contracts" / "src" / "types.ts"


@pytest.fixture(scope="module")
def openapi_doc() -> Dict[str, Any]:
    assert OPENAPI_PATH.exists(), f"OpenAPI contract missing at {OPENAPI_PATH}"
    with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return spec


def test_feat_03_openapi_yaml_syntax_and_version(openapi_doc: Dict[str, Any]) -> None:
    """Verifies that the specification adheres to OpenAPI 3.1.0 standard."""
    assert openapi_doc.get("openapi") == "3.1.0"
    info = openapi_doc.get("info", {})
    assert info.get("title") == "QUANTKUPON API"
    assert info.get("version") == "1.0.0"


def test_feat_03_all_mandatory_endpoints_declared(openapi_doc: Dict[str, Any]) -> None:
    """Verifies that all 8 required REST API path groups are declared in openapi.yaml."""
    paths = openapi_doc.get("paths", {})
    required_paths = {
        "/api/v1/categories",
        "/api/v1/events",
        "/api/v1/events/{id}/breakdown",
        "/api/v1/slips/generate",
        "/api/v1/slips/evaluate",
        "/api/v1/slips/saved",
        "/api/v1/slips/saved/{id}",
        "/api/v1/calibration/metrics",
    }
    assert required_paths.issubset(paths.keys()), f"Missing endpoints: {required_paths - paths.keys()}"

    # Verify specific HTTP methods
    assert "get" in paths["/api/v1/categories"]
    assert "get" in paths["/api/v1/events"]
    assert "post" in paths["/api/v1/slips/generate"]
    assert "post" in paths["/api/v1/slips/evaluate"]
    assert "get" in paths["/api/v1/slips/saved"]
    assert "post" in paths["/api/v1/slips/saved"]
    assert "delete" in paths["/api/v1/slips/saved/{id}"]


def test_feat_03_zero_broken_ref_pointers_in_spec(openapi_doc: Dict[str, Any]) -> None:
    """Verifies that all internal $ref pointers resolve to existing schemas."""
    schemas = openapi_doc.get("components", {}).get("schemas", {})
    broken_refs = []

    def _check_refs(node: Any, current_path: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str):
                    if v.startswith("#/components/schemas/"):
                        schema_name = v.replace("#/components/schemas/", "")
                        if schema_name not in schemas:
                            broken_refs.append((current_path, v))
                else:
                    _check_refs(v, f"{current_path}.{k}" if current_path else k)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                _check_refs(item, f"{current_path}[{idx}]")

    _check_refs(openapi_doc)
    assert not broken_refs, f"Found broken $ref pointers in OpenAPI contract: {broken_refs}"


def test_feat_03_typescript_type_definitions_completeness() -> None:
    """Verifies that generated TypeScript interfaces exist and export key schema types."""
    assert TYPES_PATH.exists(), f"TypeScript definitions file missing at {TYPES_PATH}"
    content = TYPES_PATH.read_text(encoding="utf-8")
    assert len(content) > 1000, "types.ts is unexpectedly small or empty"

    # Verify exported types and interfaces
    assert "export interface paths" in content
    assert "export interface components" in content
    assert "CategoryListResponse" in content
    assert "SlipEvaluateRequest" in content
    assert "SlipGenerateRequest" in content
    assert "EventBreakdownResponse" in content


def test_feat_03_json_schema_validation_against_fixtures(openapi_doc: Dict[str, Any]) -> None:
    """Verifies JSON schema validation of request/response models against contract."""
    resource = DRAFT202012.create_resource(openapi_doc)
    registry = Registry().with_resource("https://quantkupon.pl/openapi.yaml", resource)

    def _get_validator(schema_name: str) -> Draft202012Validator:
        ref_schema = {"$ref": f"https://quantkupon.pl/openapi.yaml#/components/schemas/{schema_name}"}
        return Draft202012Validator(ref_schema, registry=registry)

    # Validate CategoryListResponse
    category_validator = _get_validator("CategoryListResponse")
    sample_categories = {
        "categories": [
            {
                "id": 1,
                "slug": "football",
                "name_pl": "Piłka nożna",
                "is_enabled_v1": True,
                "volatility_tier": "low",
                "active_model": "dixon_coles_xg",
                "fixtures_count": 42,
                "updated_at": "2026-11-12T12:00:00Z",
            }
        ],
        "total": 1,
    }
    category_validator.validate(sample_categories)

    # Validate SlipEvaluateRequest
    eval_validator = _get_validator("SlipEvaluateRequest")
    sample_eval = {
        "selections": [
            {
                "event_id": "ev_fb_ars_che",
                "market_key": "1x2",
                "outcome_key": "home_win",
                "odds_override": 1.85,
            }
        ],
        "stake": 100.0,
        "bookmaker_mode": "standard_088",
    }
    eval_validator.validate(sample_eval)
