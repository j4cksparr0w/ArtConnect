import os, uuid
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ImagePayload:
    name: str
    bytes: bytes

class StreamlitUploadAdapter:
    @staticmethod
    def to_payload(uploaded_file: Any) -> ImagePayload:
        return ImagePayload(name=uploaded_file.name, bytes=uploaded_file.getvalue())

class LocalImageStorage:
    def __init__(self):
        self.data_dir = os.getenv("ARTCONNECT_DATA_DIR", "data")
        self.upload_dir = os.path.join(self.data_dir, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, exhibition_id: int, payload: ImagePayload) -> str:
        safe_name = payload.name.replace("/", "_").replace("\\", "_")
        filename = f"{uuid.uuid4().hex}_{safe_name}"
        folder = os.path.join(self.upload_dir, str(exhibition_id))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "wb") as f:
            f.write(payload.bytes)
        return path
