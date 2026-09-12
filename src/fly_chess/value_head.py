# Copyright (c) 2026 Martial Systems LLC
"""Scalar value heads. Graph stays frozen. Only these weights train."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


def _ridge(X: np.ndarray, y: np.ndarray, *, l2: float) -> tuple[np.ndarray, float]:
    n, d = X.shape
    X1 = np.concatenate([X, np.ones((n, 1), dtype=np.float64)], axis=1)
    A = X1.T @ X1
    A.flat[:: d + 2] += l2
    w = np.linalg.solve(A, X1.T @ y)
    return w[:-1].copy(), float(w[-1])


def ridge_from_batches(batches: list[tuple[np.ndarray, np.ndarray]], *, l2: float) -> tuple[np.ndarray, float]:
    d = int(batches[0][0].shape[1])
    dim = d + 1
    A = np.zeros((dim, dim), dtype=np.float64)
    b = np.zeros(dim, dtype=np.float64)
    for X, y in batches:
        X1 = np.concatenate([X, np.ones((X.shape[0], 1), dtype=np.float64)], axis=1)
        A += X1.T @ X1
        b += X1.T @ y
    A.flat[:: dim + 1] += l2
    w = np.linalg.solve(A, b)
    return w[:-1].copy(), float(w[-1])


@dataclass
class LinearValue:
    w: np.ndarray
    b: float
    feat_mean: np.ndarray | None = None
    feat_std: np.ndarray | None = None

    def _prep(self, X: np.ndarray) -> np.ndarray:
        if self.feat_mean is None or self.feat_std is None:
            return X
        return (X - self.feat_mean) / self.feat_std

    def predict(self, x: np.ndarray) -> float:
        return float(self.predict_many(np.asarray(x, dtype=np.float64).reshape(1, -1))[0])

    def predict_many(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        return self._prep(X) @ self.w + self.b

    @classmethod
    def fit(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        *,
        l2: float = 0.01,
        zscore: bool = False,
    ) -> "LinearValue":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        mean = std = None
        if zscore:
            mean = X.mean(axis=0)
            std = X.std(axis=0)
            std = np.where(std < 1e-8, 1.0, std)
            X = (X - mean) / std
        w, b = _ridge(X, y, l2=l2)
        return cls(w=w, b=b, feat_mean=mean, feat_std=std)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"w": self.w, "b": np.array([self.b], dtype=np.float64)}
        if self.feat_mean is not None:
            payload["feat_mean"] = self.feat_mean
            payload["feat_std"] = self.feat_std
        np.savez(path, **payload)

    @classmethod
    def load(cls, path: Path) -> "LinearValue":
        blob = np.load(path)
        mean = np.asarray(blob["feat_mean"]) if "feat_mean" in blob.files else None
        std = np.asarray(blob["feat_std"]) if "feat_std" in blob.files else None
        return cls(
            w=np.asarray(blob["w"], dtype=np.float64),
            b=float(np.asarray(blob["b"]).reshape(-1)[0]),
            feat_mean=mean,
            feat_std=std,
        )


@dataclass
class MLPValue:
    """Two-layer tanh MLP. Mix-1 nonlinear probe, not a bigger linear head."""

    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: float
    feat_mean: np.ndarray
    feat_std: np.ndarray

    def _prep(self, X: np.ndarray) -> np.ndarray:
        return (X - self.feat_mean) / self.feat_std

    def hidden(self, X: np.ndarray) -> np.ndarray:
        return np.tanh(self._prep(X) @ self.w1.T + self.b1)

    def predict_many(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        return self.hidden(X) @ self.w2 + self.b2

    def predict(self, x: np.ndarray) -> float:
        return float(self.predict_many(np.asarray(x, dtype=np.float64).reshape(1, -1))[0])

    @classmethod
    def fit(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        *,
        hidden: int = 32,
        epochs: int = 40,
        lr: float = 0.02,
        batch: int = 64,
        seed: int = 0,
        l2: float = 1e-4,
    ) -> "MLPValue":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std = np.where(std < 1e-8, 1.0, std)
        Z = (X - mean) / std
        n, d = Z.shape
        rng = np.random.default_rng(seed)
        w1 = rng.normal(0.0, 1.0 / np.sqrt(d), size=(hidden, d))
        b1 = np.zeros(hidden, dtype=np.float64)
        w2 = rng.normal(0.0, 1.0 / np.sqrt(hidden), size=(hidden,))
        b2 = 0.0
        order = np.arange(n)
        for _ in range(epochs):
            rng.shuffle(order)
            for start in range(0, n, batch):
                idx = order[start : start + batch]
                zb = Z[idx]
                yb = y[idx]
                h_lin = zb @ w1.T + b1
                h = np.tanh(h_lin)
                pred = h @ w2 + b2
                err = pred - yb
                m = max(len(idx), 1)
                g_w2 = (h.T @ err) / m + l2 * w2
                g_b2 = float(np.mean(err))
                dh = np.outer(err, w2) * (1.0 - h * h)
                g_w1 = (dh.T @ zb) / m + l2 * w1
                g_b1 = dh.mean(axis=0)
                w2 -= lr * g_w2
                b2 -= lr * g_b2
                w1 -= lr * g_w1
                b1 -= lr * g_b1
        return cls(w1=w1, b1=b1, w2=w2, b2=float(b2), feat_mean=mean, feat_std=std)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            w1=self.w1,
            b1=self.b1,
            w2=self.w2,
            b2=np.array([self.b2], dtype=np.float64),
            feat_mean=self.feat_mean,
            feat_std=self.feat_std,
        )

    @classmethod
    def load(cls, path: Path) -> "MLPValue":
        blob = np.load(path)
        return cls(
            w1=np.asarray(blob["w1"], dtype=np.float64),
            b1=np.asarray(blob["b1"], dtype=np.float64),
            w2=np.asarray(blob["w2"], dtype=np.float64),
            b2=float(np.asarray(blob["b2"]).reshape(-1)[0]),
            feat_mean=np.asarray(blob["feat_mean"], dtype=np.float64),
            feat_std=np.asarray(blob["feat_std"], dtype=np.float64),
        )
