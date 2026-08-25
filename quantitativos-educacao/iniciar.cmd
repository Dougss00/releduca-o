@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv || goto :erro
)

echo Instalando ou atualizando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :erro

echo.
echo Aplicacao disponivel em http://127.0.0.1:8000
echo Para encerrar, pressione Ctrl+C.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload
goto :fim

:erro
echo.
echo Nao foi possivel iniciar a aplicacao.
pause

:fim
endlocal
