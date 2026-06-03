# Shipment Planner

Local FastAPI app for loading cargo boxes from CSV, building container plans, and exporting results to Excel.

## What it does

- Loads cargo boxes from CSV entirely in memory.
- Builds plans for one or more containers.
- Supports balanced, free, and all-list modes.
- Exports the result to an Excel workbook.

## Run locally

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## CSV input

Upload the CSV from the UI. The browser reads the file and sends its text to the API for parsing. The server does not store uploaded files on disk.

Required columns are the same as the current cargo template used by the UI.

## Tests

```powershell
pytest -q
```
