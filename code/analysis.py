# -*- coding: utf-8 -*-
"""
测度质量检验与假设检验脚本
--------------------------------------------------
1. 描述统计：分年度/分行业均值
2. 信度检验：内部一致性（Cronbach's alpha，基于五维词频）、折半信度
3. 效度检验：与研发强度 rd 的同时效度相关；与已知组比较（高研发组 vs 低研发组）
4. 回归分析：OLS 估计 DT 对企业特征变量的回归（含年份/行业固定效应的虚拟变量）

运行：python analysis.py  （需先运行 pipeline.py）
输出：output/desc_stats.csv、reliability_validity.csv、regression_results.csv
"""
import os
import math
import numpy as np
import pandas as pd

from dictionary import DIMENSIONS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")


def cronbach_alpha(X: np.ndarray) -> float:
    """X: n 个样本 × k 个题项"""
    k = X.shape[1]
    item_var = X.var(axis=0, ddof=1).sum()
    total_var = X.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - item_var / total_var)


def ols(y, X, names):
    """普通最小二乘，返回系数、标准误、t 值、p 值（正态近似）"""
    y = np.asarray(y, float); X = np.asarray(X, float)
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sigma2 = resid @ resid / (n - k)
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * sigma2)
    t = beta / se
    from math import erf
    p = np.array([2 * (1 - 0.5 * (1 + erf(abs(v) / math.sqrt(2)))) for v in t])
    r2 = 1 - resid @ resid / ((y - y.mean()) ** 2).sum()
    return pd.DataFrame({"variable": names, "coef": beta, "se": se,
                         "t": t, "p": p.round(4), "r2": round(r2, 4)})


def main():
    panel = pd.read_csv(os.path.join(OUT_DIR, "panel_digital_transformation.csv"))
    cov = pd.read_csv(os.path.join(ROOT, "data", "firm_covariates.csv"))
    df = panel.merge(cov, on=["code", "year"], how="left")

    # ---------- 1 描述统计 ----------
    desc_year = df.groupby("year")["DT"].agg(["mean", "std", "min", "max"]).round(4)
    desc_year.to_csv(os.path.join(OUT_DIR, "desc_stats_by_year.csv"), encoding="utf-8-sig")
    desc_ind = df.groupby("industry")["DT"].agg(["mean", "std"]).round(4).sort_values("mean", ascending=False)
    desc_ind.to_csv(os.path.join(OUT_DIR, "desc_stats_by_industry.csv"), encoding="utf-8-sig")
    print("== 分年度 DT ==");  print(desc_year)
    print("== 分行业 DT ==");  print(desc_ind)

    # ---------- 2 信度 ----------
    items = df[[f"freq_{d}" for d in DIMENSIONS]].values.astype(float)
    alpha_full = cronbach_alpha(items)
    half1 = items[:, :3].sum(axis=1)
    half2 = items[:, 3:].sum(axis=1)
    r_split = np.corrcoef(half1, half2)[0, 1]
    alpha_h1, alpha_h2 = cronbach_alpha(items[:, :3]), cronbach_alpha(items[:, 3:])
    r_spearman_brown = 2 * r_split / (1 + r_split)
    print(f"Cronbach alpha={alpha_full:.3f}，折半相关={r_split:.3f}，"
          f"斯皮尔曼-布朗校正={r_spearman_brown:.3f}")

    # ---------- 3 效度 ----------
    r_rd = np.corrcoef(df["DT"], df["rd"])[0, 1]              # 同时效度
    high = df[df["rd"] >= df["rd"].median()]["DT"].mean()      # 已知组效度
    low = df[df["rd"] < df["rd"].median()]["DT"].mean()
    print(f"DT 与研发强度相关系数 r={r_rd:.3f}；高研发组均值 {high:.3f} vs 低研发组 {low:.3f}")

    pd.DataFrame({
        "指标": ["Cronbach's alpha（五维词频）", "折半信度（相关系数）",
                 "斯皮尔曼-布朗折半信度", "同时效度（DT 与 rd 相关）",
                 "已知组差异（高-低研发组 DT 均值差）"],
        "数值": [round(alpha_full, 3), round(r_split, 3),
                 round(r_spearman_brown, 3), round(r_rd, 3), round(high - low, 3)],
    }).to_csv(os.path.join(OUT_DIR, "reliability_validity.csv"),
              index=False, encoding="utf-8-sig")

    # ---------- 4 回归分析 ----------
    d = df.dropna(subset=["DT", "size", "lev", "roa", "rd"]).copy()
    y = d["DT"].values
    cols = ["size", "lev", "roa", "rd"]
    X_cols = [d[c].values for c in cols]
    names = list(cols)
    # 年份虚拟变量（以 2019 为基准）
    for yr in sorted(d["year"].unique())[1:]:
        X_cols.append((d["year"] == yr).astype(float).values); names.append(f"year_{yr}")
    # 行业虚拟变量（以第一类为基准）
    for ind in sorted(d["industry"].unique())[1:]:
        X_cols.append((d["industry"] == ind).astype(float).values); names.append(f"ind_{ind}")
    X = np.column_stack([np.ones(len(d))] + X_cols)
    names = ["const"] + names
    reg = ols(y, X, names)
    reg.to_csv(os.path.join(OUT_DIR, "regression_results.csv"), index=False, encoding="utf-8-sig")
    print("== 回归结果（因变量 DT）=="); print(reg.to_string(index=False))


if __name__ == "__main__":
    main()
