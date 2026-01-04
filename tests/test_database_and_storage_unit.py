import os

from core.database import Database
from core.storage import LocalImageStorage, StreamlitUploadAdapter


class FakeUploadedFile:
    def __init__(self, name: str, content: bytes) -> None:
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content

    def read(self) -> bytes:
        return self._content


def test_database_instance_is_singleton():
    db1 = Database.instance()
    db2 = Database.instance()

    assert db1 is db2
    assert db1.conn is db2.conn


def test_streamlit_upload_adapter_keeps_file_name():
    uploaded = FakeUploadedFile("picture.png", b"12345")

    payload = StreamlitUploadAdapter.to_payload(uploaded)

    assert payload.name == "picture.png"


def test_local_image_storage_saves_file(tmp_path):
    uploaded = FakeUploadedFile("test_image.png", b"hello-bytes")
    payload = StreamlitUploadAdapter.to_payload(uploaded)

    try:
        storage = LocalImageStorage(base_dir=str(tmp_path))
    except TypeError:
        storage = LocalImageStorage()

    path = storage.save(exhibition_id=9999, payload=payload)

    assert os.path.exists(path)

    with open(path, "rb") as f:
        content = f.read()

    assert content == b"hello-bytes"
