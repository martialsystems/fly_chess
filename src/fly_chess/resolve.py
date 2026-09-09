# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from dataclasses import dataclass, field

from fly_chess.aliases import (
    RoleSpec,
    alias_index,
    load_alias_table,
    normalize,
    required_role_names,
    role_specs,
)
from fly_chess.graph import Graph
from fly_chess.paths import RESOLVED


class ResolveError(RuntimeError):
    pass


@dataclass
class Resolved:
    roles: dict[str, list[int]]
    missing_optional: dict[str, list[str]] = field(default_factory=dict)
    source: str = ""

    def require(self, role: str) -> list[int]:
        ids = self.roles.get(role) or []
        if not ids:
            raise ResolveError(f"required role {role} has zero bodyIds")
        return ids

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "roles": {k: v for k, v in self.roles.items()},
            "missing_optional": self.missing_optional,
        }


def _match(neuron_type: str, spec: RoleSpec) -> bool:
    return normalize(neuron_type) in alias_index(spec)


def resolve_graph(graph: Graph, table: dict | None = None) -> Resolved:
    table = table or load_alias_table()
    specs = {s.name: s for s in role_specs(table)}
    roles: dict[str, list[int]] = {name: [] for name in specs}
    for neuron in graph.neurons:
        for spec in specs.values():
            if _match(neuron.type, spec):
                if spec.name == "steer_l" and neuron.side.upper() not in ("", "L"):
                    continue
                if spec.name == "steer_r" and neuron.side.upper() not in ("", "R"):
                    continue
                if spec.name == "steer_l" and neuron.side.upper() == "R":
                    continue
                if spec.name == "steer_r" and neuron.side.upper() == "L":
                    continue
                roles[spec.name].append(neuron.id)

    for role in ("steer_l", "steer_r"):
        if roles[role]:
            continue
        both = [
            n.id
            for n in graph.neurons
            if _match(n.type, specs[role])
        ]
        if both:
            mid = len(both) // 2
            if role == "steer_l":
                roles[role] = both[: max(1, mid)] or both
            else:
                roles[role] = both[mid:] or both

    missing_optional: dict[str, list[str]] = {}
    for spec in specs.values():
        if spec.required:
            continue
        if not roles[spec.name]:
            missing_optional[spec.name] = list(spec.aliases)

    for name in required_role_names(table):
        if not roles.get(name):
            raise ResolveError(f"required role {name} has zero bodyIds")

    if not roles["feed_mn"]:
        raise ResolveError("MN9 missing: Experiment 1 does not start")

    return Resolved(roles=roles, missing_optional=missing_optional, source=graph.source)


def write_resolved(resolved: Resolved, path=None) -> None:
    dest = path or RESOLVED
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(resolved.to_dict(), indent=2) + "\n", encoding="utf-8")
