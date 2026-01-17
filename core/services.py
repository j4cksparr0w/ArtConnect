import base64
import hashlib
import hmac
import os
from typing import Optional

from .repositories import UserRepo, ExhibitionRepo, InteractionRepo
from .policies import RolePolicy
from .storage import LocalImageStorage, StreamlitUploadAdapter

PBKDF2_ITERATIONS = 210_000
PBKDF2_ALG = "sha256"
PBKDF2_PREFIX = "pbkdf2_sha256"


def _pbkdf2_hash(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALG, pw.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "{}${}${}${}".format(
        PBKDF2_PREFIX,
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )


def _legacy_sha256(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _verify(pw: str, stored_hash: str) -> tuple[bool, bool]:
    if stored_hash.startswith(PBKDF2_PREFIX + "$"):
        try:
            _, iters_s, salt_b64, dk_b64 = stored_hash.split("$", 3)
            iters = int(iters_s)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(dk_b64)
            dk = hashlib.pbkdf2_hmac(PBKDF2_ALG, pw.encode("utf-8"), salt, iters)
            return (hmac.compare_digest(dk, expected), False)
        except Exception:
            return (False, False)

    return (hmac.compare_digest(_legacy_sha256(pw), stored_hash), True)


class ArtConnectService:
    def __init__(self, repos: UserRepo | ExhibitionRepo | InteractionRepo, storage: LocalImageStorage, policy: RolePolicy):
        self.repos = repos
        self.storage = storage
        self.policy = policy

    def register(self, username: str, password: str, role: str) -> None:
        self.repos.create_user(username, _pbkdf2_hash(password), role)

    def login(self, username: str, password: str) -> Optional[tuple[int, str]]:
        found = self.repos.find_user(username)
        if not found:
            return None

        uid, pw_hash, role = found
        ok, is_legacy = _verify(password, pw_hash)
        if not ok:
            return None

        if is_legacy and hasattr(self.repos, "update_password_hash"):
            try:
                new_hash = _pbkdf2_hash(password)
                self.repos.update_password_hash(uid, new_hash)  # type: ignore[attr-defined]
            except Exception:
                pass

        return (uid, role)

    def create_exhibition(self, theme: str, description: str, created_by: int) -> None:
        self.repos.create_exhibition(theme, description, created_by)

    def upload_artwork(self, exhibition_id: int, uploaded_file, uploaded_by: int) -> None:
        if not self.policy.can_upload():
            raise PermissionError("Upload is not permitted for this role.")
        payload = StreamlitUploadAdapter.to_payload(uploaded_file)
        path = self.storage.save(exhibition_id, payload)
        self.repos.add_artwork(exhibition_id, payload.name, path, uploaded_by)
