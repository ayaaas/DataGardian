"""DataGuardian quality engine (ported from notebooks/DataGuardian_Prototype.ipynb)."""
import re
import numpy as np
import pandas as pd

COUNTRY_ALIASES = {"morocco": "morocco", "maroc": "morocco", "ma": "morocco"}
SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def text_cols(df):
    return df.select_dtypes(exclude=["number", "bool", "datetime"]).columns.tolist()


def _sev(pct, high, mid):
    return "high" if pct >= high else "medium" if pct >= mid else "low"


def _issue(column, kind, severity, n, total, **extra):
    return {"column": column, "issue_type": kind, "severity": severity,
            "affected_rows": int(n), "percentage": round(n / total * 100, 2), **extra}


def detect_missing_values(df):
    return [_issue(c, "missing_values", _sev(df[c].isna().mean() * 100, 20, 10),
                   df[c].isna().sum(), len(df))
            for c in df.columns if df[c].isna().sum() > 0]


def detect_duplicates(df):
    n = int(df.duplicated().sum())
    if n == 0:
        return []
    return [_issue(None, "duplicate_rows", _sev(n / len(df) * 100, 10, 5), n, len(df))]


def detect_outliers(df):
    issues = []
    for c in df.select_dtypes(include=np.number).columns:
        s = df[c].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n = int(((s < lo) | (s > hi)).sum())
        if n:
            issues.append(_issue(c, "outliers", _sev(n / len(df) * 100, 10, 5), n, len(df),
                                 lower_bound=round(float(lo), 2), upper_bound=round(float(hi), 2)))
    return issues


def detect_categorical_inconsistencies(df, min_unique=2, max_unique=20):
    issues = []
    for c in text_cols(df):
        values = df[c].dropna().astype(str).str.strip()
        uniq = values.unique()
        if not (min_unique <= len(uniq) <= max_unique):
            continue
        groups = {}
        for v in uniq:
            groups.setdefault(re.sub(r"[^a-z0-9]", "", v.lower()), []).append(v)
        for variants in groups.values():
            if len(variants) > 1:
                issues.append(_issue(c, "categorical_inconsistency", "medium",
                                     values.isin(variants).sum(), len(df), variants=variants))
    return issues


def detect_known_aliases(df, column, alias_map):
    if column not in df.columns:
        return []
    values = df[column].dropna().astype(str).str.strip()
    groups = {}
    for v in values.unique():
        canon = alias_map.get(re.sub(r"[^a-z0-9]", "", v.lower()))
        if canon:
            groups.setdefault(canon, []).append(v)
    return [_issue(column, "categorical_inconsistency", "medium", values.isin(vs).sum(), len(df),
                   canonical=canon, variants=vs)
            for canon, vs in groups.items() if len(vs) > 1]


def calculate_quality_score(df):
    cells = df.shape[0] * df.shape[1]
    completeness = 100 * (cells - int(df.isna().sum().sum())) / cells
    uniqueness = 100 * (len(df) - int(df.duplicated().sum())) / len(df)

    checks = []
    if "age" in df.columns:
        age = pd.to_numeric(df["age"], errors="coerce")
        checks += (age.notna() & age.between(0, 120)).tolist()
    if "email" in df.columns:
        checks += df["email"].astype("string").str.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", na=False).tolist()
    validity = 100 * sum(checks) / len(checks) if checks else None

    cons = []
    for c in text_cols(df):
        v = df[c].dropna().astype(str).str.strip()
        cons += (v.str.lower().str.replace(r"[^a-z0-9]", "", regex=True) != "").tolist()
    consistency = 100 * sum(cons) / len(cons) if cons else None

    dims = {"completeness": completeness, "uniqueness": uniqueness,
            "validity": validity, "consistency": consistency}
    dims = {k: (round(float(v), 2) if v is not None else None) for k, v in dims.items()}
    avail = [v for v in dims.values() if v is not None]
    return {"overall_score": round(sum(avail) / len(avail), 2), "dimensions": dims,
            "scoring_method": "Equal-weight average of available dimensions; rules are defined by this project."}


def prioritize_issues(issues):
    out = []
    for issue in issues:
        item, w, pct = dict(issue), SEVERITY_WEIGHT.get(issue.get("severity"), 1), float(issue.get("percentage", 0))
        item["priority_score"] = round(w * pct, 2)
        item["priority"] = "high" if w == 3 or pct >= 20 else "medium" if w == 2 or pct >= 5 else "low"
        out.append(item)
    return sorted(out, key=lambda i: i["priority_score"], reverse=True)


def build_quality_report(df):
    if df.empty:
        raise ValueError("The dataset is empty.")
    issues = (detect_missing_values(df) + detect_duplicates(df) + detect_outliers(df)
              + detect_categorical_inconsistencies(df)
              + detect_known_aliases(df, "country", COUNTRY_ALIASES))
    ranked = prioritize_issues(issues)
    return {
        "dataset": {"rows": int(df.shape[0]), "columns": int(df.shape[1]),
                    "column_names": df.columns.tolist(),
                    "numeric_columns": df.select_dtypes(include=np.number).columns.tolist(),
                    "categorical_columns": text_cols(df)},
        "quality_score": calculate_quality_score(df),
        "summary": {"missing_cells": int(df.isna().sum().sum()),
                    "duplicate_rows": int(df.duplicated().sum()),
                    "detected_issues": len(ranked),
                    "high_priority_issues": sum(i["priority"] == "high" for i in ranked)},
        "issues": ranked,
    }
