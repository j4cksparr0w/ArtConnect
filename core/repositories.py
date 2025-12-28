from typing import Protocol, Optional, List
from .models import User, Exhibition, Artwork
from .database import Database

class UserRepo(Protocol):
    def create_user(self, username: str, password_hash: str, role: str) -> None: ...
    def find_user(self, username: str) -> Optional[tuple[int, str, str]]: ...  # (id, hash, role)

class ExhibitionRepo(Protocol):
    def create_exhibition(self, theme: str, description: str, created_by: int) -> None: ...
    def list_exhibitions(self) -> List[Exhibition]: ...

class InteractionRepo(Protocol):
    def add_artwork(self, exhibition_id: int, filename: str, path: str, uploaded_by: int) -> None: ...
    def list_artworks(self, exhibition_id: int) -> List[Artwork]: ...
    def toggle_like(self, user_id: int, artwork_id: int) -> None: ...
    def like_count(self, artwork_id: int) -> int: ...
    def add_comment(self, user_id: int, artwork_id: int, text: str) -> None: ...
    def list_comments(self, artwork_id: int) -> List[tuple[str, str]]: ...  # (username, text)

class SqliteRepos(UserRepo, ExhibitionRepo, InteractionRepo):
    def __init__(self):
        self.db = Database.instance().conn
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.db.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS exhibitions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          theme TEXT NOT NULL,
          description TEXT NOT NULL,
          created_by INTEGER NOT NULL,
          FOREIGN KEY(created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS artworks(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          exhibition_id INTEGER NOT NULL,
          filename TEXT NOT NULL,
          path TEXT NOT NULL,
          uploaded_by INTEGER NOT NULL,
          FOREIGN KEY(exhibition_id) REFERENCES exhibitions(id),
          FOREIGN KEY(uploaded_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS likes(
          user_id INTEGER NOT NULL,
          artwork_id INTEGER NOT NULL,
          PRIMARY KEY(user_id, artwork_id),
          FOREIGN KEY(user_id) REFERENCES users(id),
          FOREIGN KEY(artwork_id) REFERENCES artworks(id)
        );

        CREATE TABLE IF NOT EXISTS comments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          artwork_id INTEGER NOT NULL,
          text TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id),
          FOREIGN KEY(artwork_id) REFERENCES artworks(id)
        );
        """)
        self.db.commit()

    # UserRepo
    def create_user(self, username: str, password_hash: str, role: str) -> None:
        self.db.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            (username, password_hash, role)
        )
        self.db.commit()

    def find_user(self, username: str):
        row = self.db.execute(
            "SELECT id,password_hash,role FROM users WHERE username=?",
            (username,)
        ).fetchone()
        if not row:
            return None
        return (row["id"], row["password_hash"], row["role"])

    # ExhibitionRepo
    def create_exhibition(self, theme: str, description: str, created_by: int) -> None:
        self.db.execute(
            "INSERT INTO exhibitions(theme,description,created_by) VALUES(?,?,?)",
            (theme, description, created_by)
        )
        self.db.commit()

    def list_exhibitions(self):
        rows = self.db.execute("SELECT id,theme,description FROM exhibitions ORDER BY id DESC").fetchall()
        return [Exhibition(r["id"], r["theme"], r["description"]) for r in rows]

    # InteractionRepo
    def add_artwork(self, exhibition_id: int, filename: str, path: str, uploaded_by: int) -> None:
        self.db.execute(
            "INSERT INTO artworks(exhibition_id,filename,path,uploaded_by) VALUES(?,?,?,?)",
            (exhibition_id, filename, path, uploaded_by)
        )
        self.db.commit()

    def list_artworks(self, exhibition_id: int):
        rows = self.db.execute(
            "SELECT id,exhibition_id,filename,path FROM artworks WHERE exhibition_id=? ORDER BY id DESC",
            (exhibition_id,)
        ).fetchall()
        return [Artwork(r["id"], r["exhibition_id"], r["filename"], r["path"]) for r in rows]

    def toggle_like(self, user_id: int, artwork_id: int) -> None:
        cur = self.db.cursor()
        exists = cur.execute(
            "SELECT 1 FROM likes WHERE user_id=? AND artwork_id=?",
            (user_id, artwork_id)
        ).fetchone()
        if exists:
            cur.execute("DELETE FROM likes WHERE user_id=? AND artwork_id=?", (user_id, artwork_id))
        else:
            cur.execute("INSERT INTO likes(user_id,artwork_id) VALUES(?,?)", (user_id, artwork_id))
        self.db.commit()

    def like_count(self, artwork_id: int) -> int:
        row = self.db.execute("SELECT COUNT(*) AS c FROM likes WHERE artwork_id=?", (artwork_id,)).fetchone()
        return int(row["c"])

    def add_comment(self, user_id: int, artwork_id: int, text: str) -> None:
        self.db.execute(
            "INSERT INTO comments(user_id,artwork_id,text) VALUES(?,?,?)",
            (user_id, artwork_id, text)
        )
        self.db.commit()

    def list_comments(self, artwork_id: int):
        rows = self.db.execute("""
          SELECT u.username, c.text
          FROM comments c
          JOIN users u ON u.id=c.user_id
          WHERE c.artwork_id=?
          ORDER BY c.id DESC
        """, (artwork_id,)).fetchall()
        return [(r["username"], r["text"]) for r in rows]
