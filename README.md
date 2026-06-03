# Shipment Planner

Web service for loading cargo boxes from CSV, building container plans, and exporting results to Excel.

## Run locally

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## CSV input

CSV is read in the browser and sent to the API as text. The server parses it in memory and does not store uploaded files on disk.

## Tests

```powershell
pytest -q
```
