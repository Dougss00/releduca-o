# Quantitativos Educacionais

Aplicação inicial em FastAPI para enviar uma planilha Excel e gerar uma tabela com uma linha por estabelecimento, séries/anos na horizontal e subcolunas F, M e Total.

A interface usa a identidade visual da Secretaria de Educação, possui uma área de slogan e permite baixar o relatório consolidado em Excel.

## Formato esperado

A aplicação procura a aba `Consulta` (ou usa a primeira aba) e exige estas colunas:

`Estabelecimento`, `Curso`, `Aluno(a)`, `ANO - Real` e `Sexo`.

Os valores aceitos em `Sexo` são F/M e também Feminino/Masculino. Cada registro válido da planilha representa um aluno na contagem. Linhas incompletas ou com sexo inválido são informadas e ignoradas; nada é excluído do arquivo original.

## Rodar localmente

Requer Python 3.10 ou mais recente. Não é necessário ativar o ambiente virtual,
o que evita bloqueios da política de execução do PowerShell.

```powershell
cd outputs\quantitativos-educacao
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000` no navegador.

## Testes

```powershell
.venv\Scripts\python.exe -m pytest
```

Se o ambiente `.venv` já tiver sido criado, não é preciso criá-lo novamente.

## Estrutura

```text
app/
  main.py                    # rotas, upload e limites
  services/excel_processor.py # leitura, validação e consolidação
  templates/index.html       # tela principal
  static/css/style.css       # visual responsivo
  static/js/app.js           # upload e montagem da tabela
tests/                       # testes do processamento
```
