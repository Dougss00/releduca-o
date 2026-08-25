from io import BytesIO

import pandas as pd

from app.services.excel_processor import process_spreadsheet
from app.services.excel_exporter import build_summary_workbook


def make_file() -> bytes:
    data = pd.DataFrame([
        {"Estabelecimento": "Escola B", "Curso": "Fundamental", "Aluno(a)": "Ana", "ANO - Real": "1º ANO", "Sexo": "F"},
        {"Estabelecimento": "Escola A", "Curso": "Infantil", "Aluno(a)": "Bia", "ANO - Real": "CRECHE", "Sexo": "Feminino"},
        {"Estabelecimento": "Escola A", "Curso": "Infantil", "Aluno(a)": "Caio", "ANO - Real": "CRECHE", "Sexo": "M"},
    ])
    output = BytesIO()
    data.to_excel(output, index=False, sheet_name="Consulta")
    return output.getvalue()


def test_builds_one_row_per_establishment_with_dynamic_grades():
    result = process_spreadsheet(make_file())
    assert result["series"] == ["1º ANO", "CRECHE"]
    assert len(result["estabelecimentos"]) == 2
    escola_a = result["estabelecimentos"][0]
    assert escola_a["estabelecimento"] == "Escola A"
    assert escola_a["series"]["CRECHE"] == {"F": 1, "M": 1, "total": 2}
    assert escola_a["total_geral"] == 2
    assert result["resumo"]["alunos"] == 3


def test_exports_processed_data_as_excel():
    result = process_spreadsheet(make_file())
    exported = build_summary_workbook(result)
    workbook = pd.ExcelFile(BytesIO(exported))
    assert workbook.sheet_names == ["Quantitativos"]
    preview = pd.read_excel(BytesIO(exported), sheet_name="Quantitativos", header=None)
    assert preview.iloc[0, 0] == "Estabelecimento"
    assert preview.iloc[2, 0] == "Escola A"
