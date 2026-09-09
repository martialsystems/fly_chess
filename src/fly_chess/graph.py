# Copyright (c) 2026 Martial Systems LLC
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Neuron:
    id: int
    type: str
    side: str = ""
    sign: int = 1
    square: int | None = None
    body_id: int | None = None


@dataclass
class Graph:
    neurons: list[Neuron]
    pre: np.ndarray
    post: np.ndarray
    weight: np.ndarray
    source: str = "fixture"

    def __post_init__(self) -> None:
        n = len(self.neurons)
        self.pre = np.asarray(self.pre, dtype=np.int32)
        self.post = np.asarray(self.post, dtype=np.int32)
        self.weight = np.asarray(self.weight, dtype=np.float64)
        if not (len(self.pre) == len(self.post) == len(self.weight)):
            raise ValueError("edge arrays length mismatch")
        if n == 0:
            raise ValueError("empty graph")
        if self.pre.size and (self.pre.min() < 0 or self.post.min() < 0):
            raise ValueError("negative edge index")
        if self.pre.size and (int(self.pre.max()) >= n or int(self.post.max()) >= n):
            raise ValueError("edge index out of range")

    @property
    def n(self) -> int:
        return len(self.neurons)

    def types(self) -> list[str]:
        return [n.type for n in self.neurons]

    def to_dict(self) -> dict:
        def neuron_dict(n: Neuron) -> dict:
            row = {
                "id": n.id,
                "type": n.type,
                "side": n.side,
                "sign": n.sign,
                "square": n.square,
            }
            if n.body_id is not None:
                row["body_id"] = n.body_id
            return row

        return {
            "version": 1,
            "source": self.source,
            "neurons": [neuron_dict(n) for n in self.neurons],
            "edges": [
                {"pre": int(a), "post": int(b), "weight": float(w)}
                for a, b, w in zip(self.pre.tolist(), self.post.tolist(), self.weight.tolist())
            ],
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "Graph":
        neurons = [
            Neuron(
                id=int(n["id"]),
                type=str(n["type"]),
                side=str(n.get("side") or ""),
                sign=int(n.get("sign") or 1),
                square=n.get("square"),
                body_id=n.get("body_id"),
            )
            for n in raw["neurons"]
        ]
        edges = raw.get("edges") or []
        pre = np.array([e["pre"] for e in edges], dtype=np.int32)
        post = np.array([e["post"] for e in edges], dtype=np.int32)
        weight = np.array([e["weight"] for e in edges], dtype=np.float64)
        return cls(neurons=neurons, pre=pre, post=post, weight=weight, source=str(raw.get("source") or ""))
