from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.excel_processor import SpreadsheetError, process_spreadsheet
from app.services.excel_exporter import build_summary_workbook

BASE_DIR = Path(__file__).resolve().parent
MAX_FILE_SIZE = 15 * 1024 * 1024

app = FastAPI(title="Quantitativos Educacionais", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/processar")
async def process_file(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in {".xlsx", ".xls"}:
        raise HTTPException(status_code=415, detail="Envie um arquivo Excel .xlsx ou .xls.")

    content = await file.read(MAX_FILE_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo está vazio.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="O arquivo deve ter no máximo 15 MB.")

    try:
        return process_spreadsheet(content, extension)
    except SpreadsheetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Não foi possível ler a planilha.") from exc


@app.post("/api/exportar")
async def export_file(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in {".xlsx", ".xls"}:
        raise HTTPException(status_code=415, detail="Envie um arquivo Excel .xlsx ou .xls.")
    content = await file.read(MAX_FILE_SIZE + 1)
    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou maior que 15 MB.")
    try:
        report = build_summary_workbook(process_spreadsheet(content, extension))
    except SpreadsheetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Não foi possível gerar o relatório.") from exc
    headers = {"Content-Disposition": 'attachment; filename="quantitativos_educacionais.xlsx"'}
    return StreamingResponse(
        BytesIO(report),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
