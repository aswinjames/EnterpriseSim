#!/usr/bin/env python3
"""Dependency-free Draft 2020-12 validator for EnterpriseSim reference artifacts.

Loads every *.schema.json under schemas/, benchmarks/schemas/ and enterprise/schemas/
(keyed by basename and by $id), resolves cross-file $refs, and validates a data file
(a single object or an array of objects) against a named schema.

Usage:
    python3 tools/refgen/validate.py <schema-basename> <data.json> [<data2.json> ...]
    python3 tools/refgen/validate.py --all        # validate the standard registry set

Supports the JSON Schema subset used across the repo: $ref (basename or absolute $id),
allOf, type, required, properties, pattern, enum, minimum/maximum, minLength, minItems,
items, additionalProperties(false|schema), unevaluatedProperties:false, oneOf,
format(date-time).
"""
from __future__ import annotations
import json, re, sys, os, glob

HOME = os.path.expanduser("~/EnterpriseSim")
SCHEMA_DIRS = ["schemas", "benchmarks/schemas", "enterprise/schemas"]

by_file, by_id = {}, {}
for d in SCHEMA_DIRS:
    for p in glob.glob(os.path.join(HOME, d, "*.json")):
        doc = json.load(open(p))
        by_file[os.path.basename(p)] = doc
        if "$id" in doc:
            by_id[doc["$id"]] = doc

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
errors: list[str] = []


def resolve(ref, cur):
    if ref.startswith("#/"):
        n = cur
        for x in ref[2:].split("/"):
            n = n[x]
        return n, cur
    fp, _, fr = ref.partition("#")
    tgt = by_id.get(fp) or by_file.get(os.path.basename(fp))
    if tgt is None:
        raise KeyError(f"unresolvable $ref target: {fp}")
    n = tgt
    if fr:
        for x in fr[1:].split("/"):
            n = n[x]
    return n, tgt


def collect_props(s, cur, acc):
    if "$ref" in s:
        sub, d2 = resolve(s["$ref"], cur); collect_props(sub, d2, acc)
    for p in s.get("properties", {}): acc.add(p)
    for b in s.get("allOf", []): collect_props(b, cur, acc)


def tok(i, x):
    return {"object": isinstance(i, dict), "array": isinstance(i, list), "string": isinstance(i, str),
            "integer": isinstance(i, int) and not isinstance(i, bool),
            "number": isinstance(i, (int, float)) and not isinstance(i, bool),
            "boolean": isinstance(i, bool), "null": i is None}[x]


def val(i, s, cur, path):
    if "$ref" in s:
        sub, d2 = resolve(s["$ref"], cur); val(i, sub, d2, path)
    for b in s.get("allOf", []): val(i, b, cur, path)
    if "oneOf" in s:
        ok = 0
        for b in s["oneOf"]:
            sink = []; _val(i, b, cur, path, sink)
            if not sink: ok += 1
        if ok != 1: errors.append(f"{path}: oneOf matched {ok} (expected 1)")
    t = s.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        if not any(tok(i, x) for x in ts):
            errors.append(f"{path}: type {i!r} not in {ts}"); return
    if "enum" in s and i not in s["enum"]: errors.append(f"{path}: {i!r} not in enum {s['enum']}")
    if "pattern" in s and isinstance(i, str) and not re.search(s["pattern"], i):
        errors.append(f"{path}: {i!r} !~ /{s['pattern']}/")
    if s.get("format") == "date-time" and isinstance(i, str) and not DATE.match(i):
        errors.append(f"{path}: {i!r} not date-time")
    if "minimum" in s and isinstance(i, (int, float)) and not isinstance(i, bool) and i < s["minimum"]:
        errors.append(f"{path}: {i} < min {s['minimum']}")
    if "maximum" in s and isinstance(i, (int, float)) and not isinstance(i, bool) and i > s["maximum"]:
        errors.append(f"{path}: {i} > max {s['maximum']}")
    if "minLength" in s and isinstance(i, str) and len(i) < s["minLength"]:
        errors.append(f"{path}: shorter than minLength {s['minLength']}")
    if isinstance(i, dict):
        for r in s.get("required", []):
            if r not in i: errors.append(f"{path}: missing required '{r}'")
        pr = s.get("properties", {})
        for k, v in i.items():
            if k in pr: val(v, pr[k], cur, f"{path}.{k}")
        ap = s.get("additionalProperties")
        if ap is False:
            for k in i:
                if k not in pr: errors.append(f"{path}: additional property '{k}'")
        elif isinstance(ap, dict):
            for k, v in i.items():
                if k not in pr: val(v, ap, cur, f"{path}.{k}")
        if s.get("unevaluatedProperties") is False:
            allowed = set(); collect_props(s, cur, allowed)
            for k in i:
                if k not in allowed: errors.append(f"{path}: unevaluated property '{k}'")
    if isinstance(i, list):
        if "minItems" in s and len(i) < s["minItems"]: errors.append(f"{path}: fewer than minItems {s['minItems']}")
        if "items" in s:
            for j, e in enumerate(i): val(e, s["items"], cur, f"{path}[{j}]")


def _val(i, s, cur, path, sink):
    global errors
    saved = errors; errors = sink
    try: val(i, s, cur, path)
    finally: errors = saved


def validate_file(schema_basename, data_path):
    schema = by_file[schema_basename]
    data = json.load(open(data_path))
    records = data if isinstance(data, list) else [data]
    b = len(errors)
    for idx, rec in enumerate(records):
        val(rec, schema, schema, f"{os.path.basename(data_path)}[{idx}]")
    ok = len(errors) == b
    print(f"  [{'OK' if ok else 'FAIL'}] {os.path.basename(data_path)} ({len(records)} rec) vs {schema_basename}")
    return ok


REGISTRY = [
    ("application.schema.json", "enterprise/registry/applications.json"),
    ("team.schema.json", "enterprise/registry/teams.json"),
    ("repository.schema.json", "enterprise/registry/repositories.json"),
    ("release.schema.json", "enterprise/registry/releases.json"),
]

if __name__ == "__main__":
    args = sys.argv[1:]
    print(f"Loaded {len(by_file)} schemas ({len(by_id)} with $id).")
    if not args or args[0] == "--all":
        for sch, data in REGISTRY:
            validate_file(sch, os.path.join(HOME, data))
    else:
        sch = args[0]
        for dp in args[1:]:
            validate_file(sch, dp)
    if errors:
        print("\nERRORS:")
        for e in errors: print("  -", e)
        sys.exit(1)
    print("\nAll validated OK.")
