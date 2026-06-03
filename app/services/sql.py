from __future__ import annotations

from app.core.config import settings
from app.schemas import BoxItem

BOXES_QUERY = """
SELECT
    c.НаименованиеКоробки,
    c.Сумма,
    c.Объем,
    c.Длина,
    c.Ширина,
    c.Высота,
    c.Вес,
    c.Контрагент,
    c.КодНаправления,
    c.НаправлениеДоставки
FROM [S002].[Справочник_ИНФ_Коробки] c
WHERE c.Отгружен = 0
    AND c.ДатаЗакрытия IS NOT NULL
    AND c.ПометкаУдаления = 0
    AND c.IsDeleted = 0
"""


class SqlQueryService:
    def describe_capabilities(self) -> str:
        if not settings.mssql_dsn:
            return (
                "MS SQL is not configured. Set MSSQL_DSN in .env and expose only read-only "
                "views or stored procedures for the Analytics Agent."
            )
        return (
            "MS SQL DSN is configured. The MVP should execute allowlisted read-only queries "
            "through this service, with query logging and row limits."
        )

    def planner_health(self) -> tuple[bool, bool, str]:
        if not settings.mssql_dsn:
            return False, False, "MSSQL_DSN is not configured."

        try:
            import pyodbc  # type: ignore
        except ImportError:
            return True, False, "pyodbc is not installed. Add the driver dependency to enable MS SQL."

        drivers = pyodbc.drivers()
        if not drivers:
            return True, False, "pyodbc is installed, but no ODBC driver for SQL Server was found."
        return True, True, "MS SQL connection is ready for read-only planning queries."

    def fetch_planner_boxes(self) -> list[BoxItem]:
        if not settings.mssql_dsn:
            raise RuntimeError("MSSQL_DSN is not configured.")

        try:
            import pyodbc  # type: ignore
        except ImportError as error:
            raise RuntimeError("pyodbc is not installed.") from error

        connection = pyodbc.connect(settings.mssql_dsn, timeout=settings.mssql_query_timeout_seconds)
        try:
            cursor = connection.cursor()
            cursor.execute(BOXES_QUERY)
            rows = cursor.fetchall()
        finally:
            connection.close()

        boxes: list[BoxItem] = []
        for row in rows:
            boxes.append(
                BoxItem(
                    name=str(row[0] or "").strip(),
                    contractor=str(row[7] or "").strip(),
                    direction_code=str(row[8] or "").strip(),
                    amount=float(row[1] or 0),
                    volume=float(row[2] or 0),
                    length=float(row[3] or 0),
                    width=float(row[4] or 0),
                    height=float(row[5] or 0),
                    weight=float(row[6] or 0),
                    direction=str(row[9] or "UNKNOWN").strip() or "UNKNOWN",
                )
            )
        return boxes


sql_service = SqlQueryService()
