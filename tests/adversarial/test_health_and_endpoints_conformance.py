"""Adversarial Verification Suite for Health Conformance and 7 Endpoint Groups.

Verifies:
1. Conformance of FastAPI /health and /api/v1/health responses against contract.
2. Drift/gap analysis between FastAPI operational routes and packages/contracts/openapi.yaml.
3. Existence and schema completeness of all 7 mandatory endpoint groups from PROJECT.md / SCOPE.md.
4. Total $ref resolution across the entire OpenAPI 3.1 specification (zero broken pointers).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set
import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from src.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OPENAPI_PATH = REPO_ROOT / "packages" / "contracts" / "openapi.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> Dict[str, Any]:
    with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ==============================================================================
# 1. Health Endpoints Verification & Contract Conformance
# ==============================================================================


@pytest.mark.asyncio
async def test_fastapi_root_health_response_structure():
    """Tests that GET /health returns HTTP 200 with required health metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "quantkupon-api"
        assert data.get("version") == "1.0.0"


@pytest.mark.asyncio
async def test_fastapi_api_v1_health_response_structure():
    """Tests that GET /api/v1/health returns HTTP 200 with required health metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "quantkupon-api"
        assert data.get("version") == "1.0.0"


def test_contract_health_endpoints_gap_adversarial_finding(openapi_spec: Dict[str, Any]):
    """Adversarial probe: packages/contracts/openapi.yaml does NOT define /health or /api/v1/health.
    
    FINDING: While render.yaml and apps/api/src/main.py configure and test /health and
    /api/v1/health, the authoritative specification packages/contracts/openapi.yaml completely
    omits both endpoints and has no HealthResponse schema.
    """
    paths = openapi_spec.get("paths", {})
    has_root_health = "/health" in paths
    has_v1_health = "/api/v1/health" in paths
    
    # Empirically verify that openapi.yaml does NOT include these endpoints
    assert not has_root_health, "Unexpected: /health is defined in openapi.yaml"
    assert not has_v1_health, "Unexpected: /api/v1/health is defined in openapi.yaml"
    
    # Also verify components.schemas has no Health schema
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    has_health_schema = any("health" in s.lower() for s in schemas.keys())
    assert not has_health_schema, "Unexpected: health schema found in openapi.yaml"


# ==============================================================================
# 2. 7 Mandatory Endpoint Groups Verification
# ==============================================================================

MANDATORY_ENDPOINT_GROUPS = [
    ("Group 1: Categories", "/api/v1/categories", "get", "CategoryListResponse"),
    ("Group 2: Events", "/api/v1/events", "get", "EventListResponse"),
    ("Group 3: Event Breakdown", "/api/v1/events/{id}/breakdown", "get", "EventBreakdownResponse"),
    ("Group 4: Slip Generate", "/api/v1/slips/generate", "post", "SlipGenerateResponse"),
    ("Group 5: Slip Evaluate", "/api/v1/slips/evaluate", "post", "SlipEvaluateResponse"),
    ("Group 6: Calibration Metrics", "/api/v1/calibration/metrics", "get", "CalibrationMetricsResponse"),
    ("Group 7a: Saved Slips List", "/api/v1/slips/saved", "get", "SavedSlipListResponse"),
    ("Group 7b: Saved Slips Create", "/api/v1/slips/saved", "post", "SavedSlipResponse"),
    ("Group 7c: Saved Slips Delete", "/api/v1/slips/saved/{id}", "delete", "StandardSuccessResponse"),
]


@pytest.mark.parametrize("group_name,path,method,expected_resp_schema", MANDATORY_ENDPOINT_GROUPS)
def test_mandatory_endpoint_group_exists_and_complete(
    openapi_spec: Dict[str, Any], group_name, path, method, expected_resp_schema
):
    """Verifies that each of the 7 endpoint groups is present, has operationId, summary,
    and 200/201 response pointing to the expected response schema.
    """
    paths = openapi_spec.get("paths", {})
    assert path in paths, f"{group_name}: Path '{path}' missing from openapi.yaml"
    
    path_item = paths[path]
    assert method in path_item, f"{group_name}: Method '{method.upper()}' missing for path '{path}'"
    
    operation = path_item[method]
    assert "operationId" in operation, f"{group_name}: Missing operationId"
    assert "summary" in operation, f"{group_name}: Missing summary"
    assert "responses" in operation, f"{group_name}: Missing responses definition"
    
    responses = operation["responses"]
    success_code = "201" if (path == "/api/v1/slips/saved" and method == "post") else "200"
    assert success_code in responses, f"{group_name}: Missing success status code {success_code}"
    
    success_resp = responses[success_code]
    content = success_resp.get("content", {})
    assert "application/json" in content, f"{group_name}: Missing application/json response content"
    
    schema = content["application/json"].get("schema", {})
    assert "$ref" in schema, f"{group_name}: Missing $ref schema in success response"
    assert schema["$ref"] == f"#/components/schemas/{expected_resp_schema}", (
        f"{group_name}: Expected ref '#/components/schemas/{expected_resp_schema}', got '{schema['$ref']}'"
    )


def test_post_endpoints_have_request_bodies(openapi_spec: Dict[str, Any]):
    """Verifies that all POST endpoints have required requestBody definitions."""
    post_checks = [
        ("/api/v1/slips/generate", "SlipGenerateRequest"),
        ("/api/v1/slips/evaluate", "SlipEvaluateRequest"),
        ("/api/v1/slips/saved", "SaveSlipRequest"),
    ]
    paths = openapi_spec.get("paths", {})
    for path, expected_req_schema in post_checks:
        op = paths[path]["post"]
        assert "requestBody" in op, f"POST {path} missing requestBody"
        assert op["requestBody"].get("required") is True, f"POST {path} requestBody not marked required"
        content = op["requestBody"].get("content", {})
        assert "application/json" in content, f"POST {path} missing application/json in requestBody"
        schema = content["application/json"].get("schema", {})
        assert schema.get("$ref") == f"#/components/schemas/{expected_req_schema}", (
            f"POST {path}: Expected request schema {expected_req_schema}"
        )


def test_all_schema_and_response_refs_resolve(openapi_spec: Dict[str, Any]):
    """Recursively checks that EVERY $ref in openapi.yaml resolves to an existing component."""
    components = openapi_spec.get("components", {})
    schemas = components.get("schemas", {})
    responses = components.get("responses", {})
    
    unresolved_refs: List[str] = []

    def check_node(node: Any, path_trace: str):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str):
                    if v.startswith("#/components/schemas/"):
                        sname = v.replace("#/components/schemas/", "")
                        if sname not in schemas:
                            unresolved_refs.append(f"{path_trace} -> {v}")
                    elif v.startswith("#/components/responses/"):
                        rname = v.replace("#/components/responses/", "")
                        if rname not in responses:
                            unresolved_refs.append(f"{path_trace} -> {v}")
                    else:
                        unresolved_refs.append(f"{path_trace} -> unknown ref scheme {v}")
                else:
                    check_node(v, f"{path_trace}.{k}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                check_node(item, f"{path_trace}[{i}]")

    check_node(openapi_spec, "root")
    assert len(unresolved_refs) == 0, f"Found unresolved $ref pointers: {unresolved_refs}"


def test_error_responses_standardized(openapi_spec: Dict[str, Any]):
    """Verifies standard 400, 404, 500 error responses are properly defined."""
    responses = openapi_spec.get("components", {}).get("responses", {})
    assert "BadRequestError" in responses
    assert "NotFoundError" in responses
    assert "InternalServerError" in responses
    
    # Ensure they use ErrorResponse schema
    for rname in ["BadRequestError", "NotFoundError", "InternalServerError"]:
        r = responses[rname]
        schema = r.get("content", {}).get("application/json", {}).get("schema", {})
        assert schema.get("$ref") == "#/components/schemas/ErrorResponse"
