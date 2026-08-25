from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["Estabelecimento", "Curso", "Aluno(a)", "ANO - Real", "Sexo"]


class SpreadsheetError(ValueError):
    """Erro de validação compreensível para quem enviou a planilha."""


def _clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace("", pd.NA)


def _normalize_sex(value: Any) -> str | None:
    normalized = str(value).strip().upper()
    if normalized in {"F", "FEMININO", "FEMININA"}:
        return "F"
    if normalized in {"M", "MASCULINO", "MASCULINA"}:
        return "M"
    return None


def _read_excel(content: bytes, extension: str) -> pd.DataFrame:
    engine = "openpyxl" if extension == ".xlsx" else "xlrd"
    workbook = pd.ExcelFile(BytesIO(content), engine=engine)
    sheet = "Consulta" if "Consulta" in workbook.sheet_names else workbook.sheet_names[0]
    return pd.read_excel(workbook, sheet_name=sheet)


def process_spreadsheet(content: bytes, extension: str = ".xlsx") -> dict[str, Any]:
    dataframe = _read_excel(content, extension)
    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        raise SpreadsheetError("Colunas obrigatórias ausentes: " + ", ".join(missing) + ".")

    data = dataframe[REQUIRED_COLUMNS].copy()
    for column in ["Estabelecimento", "Curso", "Aluno(a)", "ANO - Real"]:
        data[column] = _clean_text(data[column])
    data["Sexo"] = data["Sexo"].map(_normalize_sex)

    valid = data.dropna(subset=["Estabelecimento", "Aluno(a)", "ANO - Real", "Sexo"]).copy()
    ignored_rows = int(len(data) - len(valid))
    if valid.empty:
        raise SpreadsheetError("Nenhum registro válido foi encontrado na planilha.")

    # A ordem apresentada na planilha é preservada para evitar uma ordenação
    # alfabética pouco natural (por exemplo, 10º ANO antes de 2º ANO).
    grades = valid["ANO - Real"].drop_duplicates().tolist()
    establishments = sorted(valid["Estabelecimento"].drop_duplicates().tolist(), key=str.casefold)

    grouped = valid.groupby(["Estabelecimento", "ANO - Real", "Sexo"], sort=False).size()
    rows: list[dict[str, Any]] = []
    for establishment in establishments:
        by_grade: dict[str, dict[str, int]] = {}
        total_f = 0
        total_m = 0
        for grade in grades:
            female = int(grouped.get((establishment, grade, "F"), 0))
            male = int(grouped.get((establishment, grade, "M"), 0))
            by_grade[grade] = {"F": female, "M": male, "total": female + male}
            total_f += female
            total_m += male
        rows.append(
            {
                "estabelecimento": establishment,
                "series": by_grade,
                "total_f": total_f,
                "total_m": total_m,
                "total_geral": total_f + total_m,
            }
        )

    network_f = int((valid["Sexo"] == "F").sum())
    network_m = int((valid["Sexo"] == "M").sum())
    return {
        "series": grades,
        "estabelecimentos": rows,
        "resumo": {
            "alunos": network_f + network_m,
            "estabelecimentos": len(establishments),
            "total_f": network_f,
            "total_m": network_m,
            "linhas_ignoradas": ignored_rows,
        },
    }
