from fastapi.testclient import TestClient

from app.main import app


def test_csv_upload_rejects_large_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/shipment-planner/boxes/upload",
        json={
            "filename": "boxes.csv",
            "content": "x" * (5 * 1024 * 1024 + 1),
        },
    )

    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]


def test_csv_parser_rejects_too_many_rows(monkeypatch) -> None:
    import app.services.csv_boxes as csv_boxes

    monkeypatch.setattr(csv_boxes, "MAX_CSV_ROWS", 3)
    client = TestClient(app)
    header = "НаименованиеКоробки,Сумма,Объем,Длина,Ширина,Высота,Вес,Контрагент,КодНаправления,НаправлениеДоставки\n"
    row = "BOX,1,1,1,1,1,1,C,SEA,SEA\n"
    content = header + row * 4
    response = client.post(
        "/api/shipment-planner/boxes/upload",
        json={"filename": "boxes.csv", "content": content},
    )

    assert response.status_code == 400
    assert "Максимум" in response.json()["detail"]
