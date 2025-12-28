import os, sqlite3
from typing import Optional

class Database:
    _instance: Optional["Database"] = None

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    @classmethod
    def instance(cls) -> "Database":
        if cls._instance is None:
            data_dir = os.getenv("ARTCONNECT_DATA_DIR", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "artconnect.db")
            cls._instance = cls(db_path)
        return cls._instance
