"""房价建模与可解释性分析。"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .utils import ensure_dir, write_json


def _design_matrix(df: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, list[str]]:
    use_cols = [col for col in features if col in df.columns]
    return df[use_cols].to_numpy(dtype=float), use_cols


def ols_numpy(X: np.ndarray, y: np.ndarray) -> dict[str, float | np.ndarray]:
    X = np.column_stack([np.ones(len(X)), X])
    coefficients, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coefficients
    residual = y - y_hat
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rmse = float(np.sqrt(np.mean(residual**2)))
    mae = float(np.mean(np.abs(residual)))
    return {"coefficients": coefficients, "r2": r2, "rmse": rmse, "mae": mae}


def run_ols_fallback(
    feature_csv: Path,
    target: str = "block_price",
    features: list[str] | None = None,
) -> dict[str, float | np.ndarray]:
    df = pd.read_csv(feature_csv)
    if target not in df.columns:
        raise ValueError(f"缺少目标列: {target}")
    if features is None:
        features = [col for col in df.columns if col not in {target, "block_id", "city", "year"}]
    X, used = _design_matrix(df, features)
    y = df[target].to_numpy(dtype=float)
    result = ols_numpy(X, y)
    result["features"] = ["intercept"] + used
    return result


def run_modeling(
    feature_csv: Path | None = None,
    output_dir: Path | None = None,
    target: str = "block_price",
) -> Path:
    feature_csv = Path(feature_csv or config.OUTPUT_FEATURE_MATRIX)
    output_dir = output_dir or config.REPORTS_DIR
    ensure_dir(output_dir)

    if not feature_csv.exists():
        raise FileNotFoundError(
            f"特征矩阵不存在: {feature_csv}\n"
            "请先完成 03_build_blocks.py 和 04_build_features.py，生成街区特征矩阵。"
        )

    try:
        import sklearn  # noqa: F401
        has_sklearn = True
    except ImportError:
        has_sklearn = False

    if has_sklearn:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split

        df = pd.read_csv(feature_csv)
        features = [col for col in df.columns if col not in {target, "block_id", "city", "year"}]
        X = df[features].to_numpy(dtype=float)
        y = df[target].to_numpy(dtype=float)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=config.RANDOM_SEED
        )
        model = RandomForestRegressor(n_estimators=300, random_state=config.RANDOM_SEED, n_jobs=-1)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {
            "model": "RandomForest",
            "r2": float(r2_score(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
            "mae": float(mean_absolute_error(y_test, pred)),
        }
    else:
        metrics = {
            "model": "OLS_numpy_fallback",
            **{
                key: value
                for key, value in run_ols_fallback(feature_csv, target=target).items()
                if key in {"r2", "rmse", "mae"}
            },
        }

    out = output_dir / "model_metrics.csv"
    pd.DataFrame([metrics]).to_csv(out, index=False, encoding="utf-8-sig")
    write_json(output_dir / "model_metrics.json", metrics)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--target", default="block_price")
    args = parser.parse_args()
    run_modeling(args.feature_csv, args.output_dir, args.target)


if __name__ == "__main__":
    main()
