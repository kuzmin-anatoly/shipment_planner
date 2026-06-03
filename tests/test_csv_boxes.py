from app.services.csv_boxes import parse_boxes_csv


def test_parse_boxes_csv() -> None:
    content = """
НаименованиеКоробки,Сумма,Объем,Длина,Ширина,Высота,Вес,Контрагент,КодНаправления,НаправлениеДоставки
BOX-1,1000,1.5,100,50,50,20,Client A,SEA-0,SEA
BOX-2,2000,2.5,120,60,55,30,Client B,LAND-1,LAND
""".strip().encode("utf-8")

    boxes = parse_boxes_csv(content)

    assert len(boxes) == 2
    assert boxes[0].name == "BOX-1"
    assert boxes[0].contractor == "Client A"
    assert boxes[0].direction_code == "SEA-0"
    assert boxes[0].amount == 1000
    assert boxes[1].direction == "LAND"
