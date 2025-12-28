# Design Patterns (3)

This project intentionally uses 3 patterns: 1 creational, 1 structural, 1 behavioral.

## 1) Singleton (Creational)
**Where:** `core/database.py`  
**Why:** ensures a single shared SQLite connection across the app.

- `Database.instance()` returns the same Database object (single instance).

## 2) Adapter (Structural)
**Where:** `core/storage.py`  
**Why:** Streamlit `UploadedFile` is a UI-specific type. We adapt it to a simple domain payload.

- `StreamlitUploadAdapter.to_payload(uploaded_file)` converts Streamlit upload into `ImagePayload`.

## 3) Strategy (Behavioral)
**Where:** `core/policies.py` + used in `app.py`  
**Why:** different roles (mentor/student) have different permissions without `if/else` scattered everywhere.

- `MentorPolicy.can_upload() -> True`
- `StudentPolicy.can_upload() -> False`
- `policy_for(role)` selects the active strategy.
