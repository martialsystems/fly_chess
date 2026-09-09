# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fly_chess.paths import ALIASES


@dataclass(frozen=True)
class RoleSpec:
    name: str
    required: bool
    aliases: tuple[str, ...]


def load_alias_table(path: Path | None = None) -> dict:
    p = path or ALIASES
    return json.loads(p.read_text(encoding="utf-8"))


def role_specs(table: dict | None = None) -> list[RoleSpec]:
    table = table or load_alias_table()
    out: list[RoleSpec] = []
    for name, spec in table["roles"].items():
        out.append(
            RoleSpec(
                name=name,
                required=bool(spec.get("required")),
                aliases=tuple(spec.get("aliases") or ()),
            )
        )
    return out


def required_role_names(table: dict | None = None) -> tuple[str, ...]:
    table = table or load_alias_table()
    return tuple(table["required_roles"])


def normalize(name: str) -> str:
    return re_sub_space(name).casefold()


def re_sub_space(name: str) -> str:
    return " ".join((name or "").replace("_", " ").replace("-", " ").split())


def alias_index(spec: RoleSpec) -> set[str]:
    return {normalize(a) for a in spec.aliases} | {normalize(spec.name)}
