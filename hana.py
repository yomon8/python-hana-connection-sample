import csv
from contextlib import contextmanager
from typing import IO, Generator

import pandas as pd
from hdbcli import dbapi
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"


# Read .env file
class HanaConnectionSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        frozen=True,
        case_sensitive=False,
    )
    hdb_host: str
    hdb_port: int
    hdb_user: str
    hdb_password: str


@contextmanager
def hana_connection(
    settings: HanaConnectionSettings = HanaConnectionSettings(),
) -> Generator[dbapi.Connection, None, None]:
    conn = dbapi.connect(
        address=settings.hdb_host,
        port=settings.hdb_port,
        user=settings.hdb_user,
        password=settings.hdb_password,
    )
    try:
        yield conn
    finally:
        conn.close()


# Select as CSV format
def select_all_as_csv(select_sql: str, output: IO) -> None:
    with hana_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(operation=select_sql)
            writer = csv.writer(output)
            column_names = [d[0] for d in cursor.description]
            writer.writerow(column_names)
            values = [r.column_values for r in cursor.fetchall()]
            writer.writerows(values)


# Select as Pandas Dataframe format
def select_all_as_df(select_sql: str) -> pd.DataFrame:
    with hana_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(operation=select_sql)
            column_names = [d[0] for d in cursor.description]
            data: dict[str, list] = {c: [] for c in column_names}
            for row in cursor.fetchall():
                for i, c in enumerate(row.column_names):
                    data[c].append(row[i])
            df = pd.DataFrame(data=data)
            return df
