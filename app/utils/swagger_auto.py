"""
Minimal OpenAPI/Swagger generator for this Flask app.

Goal:
- Keep Swagger as a generated artifact from real API routes.
- Parse endpoint docstrings to enrich spec with summary/description/params/responses.

Docstring convention (already used in app/api/*):

    GET /api/incomes/
    Summary: List incomes with optional sorting

    Query:
      - sort: "income_date" | "amount" (default: "income_date")
      - order: "asc" | "desc" (default: "desc")

    Path:
      income_id: uuid

    Request:
      { ... json example ... }

    Responses:
      200:
        data: {...}
      404:
        data: null
        error: {...}

This generator does NOT infer schemas automatically. It focuses on:
- paths + methods
- summary/description
- query/path parameters
- response codes with text descriptions
"""

from __future__ import annotations

import json
import os
import re
from inspect import getdoc
from typing import Any, Dict, List, Optional, Tuple


SECTION_RE = re.compile(r"^(Summary|Query|Path|Request|Responses)\s*:\s*$", re.I)


def flask_rule_to_openapi(rule: str) -> str:
    """
    Convert Flask style variables:
      /api/incomes/<uuid:income_id> -> /api/incomes/{income_id}
      /api/budgets/<month> -> /api/budgets/{month}
    """
    def repl(m: re.Match) -> str:
        raw = m.group(1)
        if ":" in raw:
            _, name = raw.split(":", 1)
        else:
            name = raw
        return "{" + name + "}"

    return re.sub(r"<([^>]+)>", repl, rule)


def _split_sections(doc: str) -> Dict[str, str]:
    """
    Splits a docstring into named sections based on SECTION_RE.
    Returns dict {section_name_lower: content}.
    """
    sections: Dict[str, str] = {}
    current: Optional[str] = None
    buf: List[str] = []

    for line in doc.splitlines():
        stripped = line.strip()
        m = SECTION_RE.match(stripped)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).lower()
            buf = []
        else:
            if current is not None:
                buf.append(line)

    if current is not None:
        sections[current] = "\n".join(buf).strip()

    return sections


def _parse_param_lines(block: str) -> List[Dict[str, Any]]:
    """
    Parse parameter blocks.

    Accepts lines like:
      - sort: "income_date" | "amount" (default: "income_date")
      income_id: uuid
      month: "YYYY-MM"

    Returns a list of OpenAPI-ish param dicts (without 'in' and 'required').
    """
    params: List[Dict[str, Any]] = []

    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue

        # allow "- name: desc" style
        line = line.lstrip("-").strip()

        if ":" not in line:
            continue

        name, rest = line.split(":", 1)
        name = name.strip()
        rest = rest.strip()

        schema: Dict[str, Any] = {"type": "string"}

        low = rest.lower()
        if "uuid" in low:
            schema = {"type": "string", "format": "uuid"}
        elif "int" in low or "integer" in low:
            schema = {"type": "integer"}
        elif "number" in low or "float" in low or "decimal" in low:
            schema = {"type": "number"}
        elif "bool" in low or "boolean" in low:
            schema = {"type": "boolean"}

        params.append(
            {
                "name": name,
                "description": rest,
                "schema": schema,
            }
        )

    return params


def _parse_responses(block: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse Responses block into OpenAPI responses.

    Example:
      200:
        data: {...}
      404:
        data: null
        error: {...}

    We store everything as description text; schema inference is not done here.
    """
    responses: Dict[str, Dict[str, Any]] = {}

    current_code: Optional[str] = None
    desc_lines: List[str] = []

    for raw in block.splitlines():
        line = raw.rstrip()
        m = re.match(r"^\s*(\d{3})\s*:\s*$", line)
        if m:
            if current_code is not None:
                desc = "\n".join(desc_lines).strip() or "Success"
                responses[current_code] = {"description": desc}
            current_code = m.group(1)
            desc_lines = []
        else:
            if current_code is not None:
                desc_lines.append(line)

    if current_code is not None:
        desc = "\n".join(desc_lines).strip() or "Success"
        responses[current_code] = {"description": desc}

    return responses


def parse_doc(doc: str) -> Dict[str, Any]:
    """
    Parse endpoint docstring into:
      summary, description, query_params, path_params, responses
    """
    if not doc:
        return {}

    sections = _split_sections(doc)

    summary = sections.get("summary")
    description: Optional[str] = None

    if summary:
        # take text after "Summary:" until next section
        after = doc.split("Summary:", 1)[-1].strip()
        # cut at next section header if any
        cut = SECTION_RE.split(after)[0].strip()
        description = cut if cut and cut != summary else None

    query_params = _parse_param_lines(sections.get("query", "")) if "query" in sections else []
    path_params = _parse_param_lines(sections.get("path", "")) if "path" in sections else []
    responses = _parse_responses(sections.get("responses", "")) if "responses" in sections else {}

    return {
        "summary": summary,
        "description": description,
        "query_params": query_params,
        "path_params": path_params,
        "responses": responses,
    }


def _guess_tag(openapi_path: str) -> str:
    """
    /api/incomes/{id} -> incomes
    /api/receipts/{id}/items -> receipts
    """
    parts = [p for p in openapi_path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return "api"


def generate_spec(app, title: str = "Budget API", version: str = "0.1.0") -> Dict[str, Any]:
    """
    Build OpenAPI spec dict by introspecting Flask url_map and docstrings.
    """
    spec: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": title, "version": version},
        "paths": {},
    }

    for rule in app.url_map.iter_rules():
        path = rule.rule

        # Only document API routes
        if not path.startswith("/api"):
            continue
        # Skip swagger UI itself
        if path.startswith(app.config.get("SWAGGER_URL", "/api/docs")):
            continue

        openapi_path = flask_rule_to_openapi(path)
        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})

        if openapi_path not in spec["paths"]:
            spec["paths"][openapi_path] = {}

        view_func = app.view_functions.get(rule.endpoint)
        doc = getdoc(view_func) if view_func else ""
        meta = parse_doc(doc or "")

        tag = _guess_tag(openapi_path)

        for method in methods:
            op: Dict[str, Any] = {
                "tags": [tag],
                "summary": meta.get("summary") or f"{method} {openapi_path}",
            }

            if meta.get("description"):
                op["description"] = meta["description"]

            parameters: List[Dict[str, Any]] = []

            for p in meta.get("path_params", []):
                p = dict(p)
                p["in"] = "path"
                p["required"] = True
                parameters.append(p)

            for p in meta.get("query_params", []):
                p = dict(p)
                p["in"] = "query"
                p["required"] = False
                parameters.append(p)

            if parameters:
                op["parameters"] = parameters

            if meta.get("responses"):
                op["responses"] = meta["responses"]
            else:
                op["responses"] = {"200": {"description": "Success"}}

            spec["paths"][openapi_path][method.lower()] = op

    return spec


def write_swagger_json(app, out_path: Optional[str] = None) -> str:
    """
    Generate spec and write into static/swagger.json.
    Returns the final path.
    """
    if out_path is None:
        # Default to app/static/swagger.json
        static_dir = os.path.join(app.root_path, "static")
        out_path = os.path.join(static_dir, "swagger.json")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    spec = generate_spec(
        app,
        title=app.config.get("SWAGGER_TITLE", "Budget API"),
        version=app.config.get("SWAGGER_VERSION", "0.1.0"),
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    return out_path
