import hashlib
from typing import Optional
from .repositories import UserRepo, ExhibitionRepo, InteractionRepo
from .policies import RolePolicy
from .storage import LocalImageStorage, StreamlitUploadAdapter

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

class ArtConnectService:
    def __init__(self, repos: UserRepo | ExhibitionRepo | InteractionRepo, storage: LocalImageStorage, policy: RolePolicy):
        self.repos = repos
        self.storage = storage
        self.policy = policy

    def register(self, username: str, password: str, role: str) -> None:
        self.repos.create_user(username, _hash(password), role)

    def login(self, username: str, password: str) -> Optional[tuple[int, str]]:
        found = self.repos.find_user(username)
        if not found:
            return None
        uid, pw_hash, role = found
        if pw_hash != _hash(password):
            return None
        return (uid, role)

    def create_exhibition(self, theme: str, description: str, created_by: int) -> None:
        self.repos.create_exhibition(theme, description, created_by)

    def upload_artwork(self, exhibition_id: int, uploaded_file, uploaded_by: int) -> None:
        if not self.policy.can_upload():
            raise PermissionError("Upload is not permitted for this role.")
        payload = StreamlitUploadAdapter.to_payload(uploaded_file)
        path = self.storage.save(exhibition_id, payload)
        self.repos.add_artwork(exhibition_id, payload.name, path, uploaded_by)
