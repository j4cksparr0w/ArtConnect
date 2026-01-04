import pytest

from core.services import ArtConnectService


class DummyRepos:
    def __init__(self) -> None:
        self.users = {}
        self.next_user_id = 1
        self.artworks = []

    def create_user(self, username: str, password_hash: str, role: str) -> None:
        self.users[username] = (self.next_user_id, password_hash, role)
        self.next_user_id += 1

    def find_user(self, username: str):
        return self.users.get(username)

    def add_artwork(
        self,
        exhibition_id: int,
        filename: str,
        path: str,
        uploaded_by: int,
    ) -> None:
        self.artworks.append(
            {
                "exhibition_id": exhibition_id,
                "filename": filename,
                "path": path,
                "uploaded_by": uploaded_by,
            }
        )


class DummyStorage:
    def __init__(self) -> None:
        self.saved = []

    def save(self, exhibition_id: int, payload) -> str:
        path = f"/fake/{exhibition_id}/{payload.name}"
        self.saved.append((exhibition_id, payload.name, path))
        return path


class AllowPolicy:
    def can_upload(self) -> bool:
        return True


class DenyPolicy:
    def can_upload(self) -> bool:
        return False


class FakeUploadedFile:
    def __init__(self, name: str, content: bytes = b"dummy-bytes") -> None:
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content

    def read(self) -> bytes:
        return self._content


def _service_with(policy) -> ArtConnectService:
    repos = DummyRepos()
    storage = DummyStorage()
    return ArtConnectService(repos, storage, policy)


def test_register_and_login_success():
    service = _service_with(AllowPolicy())

    service.register("user1", "secret", "student")

    result = service.login("user1", "secret")
    assert result is not None

    uid, role = result
    assert uid == 1
    assert role == "student"


def test_login_wrong_password_returns_none():
    service = _service_with(AllowPolicy())

    service.register("user2", "secret", "mentor")

    assert service.login("user2", "wrong") is None


def test_login_unknown_user_returns_none():
    service = _service_with(AllowPolicy())

    assert service.login("unknown_user", "pw") is None


def test_upload_artwork_allowed():
    service = _service_with(AllowPolicy())

    service.register("artist", "pw", "mentor")
    uid, _ = service.login("artist", "pw")

    uploaded = FakeUploadedFile("work.png", b"image-bytes")
    service.upload_artwork(exhibition_id=1, uploaded_file=uploaded, uploaded_by=uid)

    repos: DummyRepos = service.repos 
    storage: DummyStorage = service.storage 

    assert len(repos.artworks) == 1
    assert len(storage.saved) == 1
    assert storage.saved[0][1] == "work.png"


def test_upload_artwork_denied_raises():
    service = _service_with(DenyPolicy())

    service.register("student", "pw", "student")
    uid, _ = service.login("student", "pw")

    uploaded = FakeUploadedFile("blocked.png")

    with pytest.raises(PermissionError):
        service.upload_artwork(exhibition_id=1, uploaded_file=uploaded, uploaded_by=uid)

    repos: DummyRepos = service.repos 
    storage: DummyStorage = service.storage

    assert repos.artworks == []
    assert storage.saved == []
