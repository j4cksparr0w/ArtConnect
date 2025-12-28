# Database (SQLite)

- ArtConnect uses SQLite for minimal setup and portability.
- Schema is created on app start via `SqliteRepos._init_schema()`.

## Why SQLite?
- Single file database (no server needed)
- Enough for login, exhibitions, artworks, likes, comments

## Singleton
- `Database.instance()` ensures a single shared DB connection.
