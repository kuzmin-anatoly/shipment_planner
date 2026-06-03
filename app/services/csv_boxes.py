from __future__ import annotations

import csv
import io

from app.schemas import BoxItem


CSV_COLUMNS = [
    "НаименованиеКоробки",
    "Сумма",
    "Объем",
    "Длина",
    "Ширина",
    "Высота",
    "Вес",
    "Контрагент",
    "КодНаправления",
    "НаправлениеДоставки",
]


def parse_boxes_csv(content: bytes) -> list[BoxItem]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not set(CSV_COLUMNS).issubset(set(reader.fieldnames)):
        raise ValueError("CSV должен содержать колонки: " + ", ".join(CSV_COLUMNS))

    boxes: list[BoxItem] = []
    for row in reader:
        if not any((value or "").strip() for value in row.values()):
            continue
        boxes.append(
            BoxItem(
                name=(row["НаименованиеКоробки"] or "").strip(),
                contractor=(row["Контрагент"] or "").strip(),
                direction_code=(row["КодНаправления"] or "").strip(),
                amount=_to_float(row["Сумма"]),
                volume=_to_float(row["Объем"]),
                length=_to_float(row["Длина"]),
                width=_to_float(row["Ширина"]),
                height=_to_float(row["Высота"]),
                weight=_to_float(row["Вес"]),
                direction=(row["НаправлениеДоставки"] or "UNKNOWN").strip() or "UNKNOWN",
            )
        )
    return boxes


def _to_float(value: str | None) -> float:
    if value is None:
        return 0.0
    normalized = value.strip().replace(" ", "").replace(",", ".")
    return float(normalized) if normalized else 0.0
