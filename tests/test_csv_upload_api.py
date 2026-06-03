from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_csv_upload_uses_memory_only(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("filesystem should not be used for CSV uploads")

    monkeypatch.setattr("builtins.open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called, raising=False)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called, raising=False)

    client = TestClient(app)
    response = client.post(
        "/api/shipment-planner/boxes/upload",
        json={
            "filename": "boxes.csv",
            "content": (
                "НаименованиеКоробки,Сумма,Объем,Длина,Ширина,Высота,Вес,Контрагент,КодНаправления,НаправлениеДоставки\n"
                "BOX-1,1000,1.5,100,50,50,20,Client A,SEA-0,SEA\n"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["source"] == "csv"
    assert response.json()["count"] == 1
