import pytest
from core.services import ArtConnectService

class DummyRepos:
    def __init__(self):
        self.users = {}
        self.next_user_id = 1
        self.artworks = []
    def create_user(self, username, password_hash, role):
        self.users[username] = (self.next_user_id, password_hash, role)
        self.next_user_id += 1
    def find_user(self, username):
        return self.users.get(username)
    def add_artwork(self, exhibition_id, filename, path, uploaded_by):
        self.artworks.append(
            {"exhibition_id": exhibition_id, "filename": filename, "path": path, "uploaded_by": uploaded_by}
        )

class DummyStorage:
    def __init__(self):
        self.saved = []
    def save(self, exhibition_id, payload):
        path = f"/fake/{exhibition_id}/{payload.name}"
        self.saved.append((exhibition_id, payload.name, path))
        return path

class AllowPolicy:
    def can_upload(self):
        return True

class DenyPolicy:
    def can_upload(self):
        return False

class FakeUploadedFile:
    def __init__(self, name, content: bytes = b"data"):
        self.name = name
        self._content = content
    def getvalue(self):
        return self._content
    def read(self):
        return self._content

def make_service(policy):
    repos = DummyRepos()
    storage = DummyStorage()
    return ArtConnectService(repos, storage, policy)

def test_register_and_login_success():
    s = make_service(AllowPolicy())
    s.register("u1", "pw", "student")
    uid, role = s.login("u1", "pw")
    assert uid == 1
    assert role == "student"

def test_login_wrong_password_returns_none():
    s = make_service(AllowPolicy())
    s.register("u2", "pw", "mentor")
    assert s.login("u2", "wrong") is None

def test_login_unknown_user_returns_none():
    s = make_service(AllowPolicy())
    assert s.login("x", "pw") is None

def test_upload_artwork_allowed():
    s = make_service(AllowPolicy())
    s.register("artist", "pw", "mentor")
    uid, _ = s.login("artist", "pw")
    uploaded = FakeUploadedFile("work.png", b"img")
    s.upload_artwork(1, uploaded, uid)
    repos = s.repos
    storage = s.storage
    assert len(repos.artworks) == 1
    assert len(storage.saved) == 1
    assert storage.saved[0][1] == "work.png"

def test_upload_artwork_denied_raises():
    s = make_service(DenyPolicy())
    s.register("student", "pw", "student")
    uid, _ = s.login("student", "pw")
    uploaded = FakeUploadedFile("blocked.png", b"img")
    with pytest.raises(PermissionError):
        s.upload_artwork(1, uploaded, uid)
    repos = s.repos
    storage = s.storage
    assert repos.artworks == []
    assert storage.saved == []
