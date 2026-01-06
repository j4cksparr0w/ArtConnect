import uuid
from core.repositories import SqliteRepos
from core.services import ArtConnectService
from core.storage import LocalImageStorage
from core.policies import MentorPolicy

class FakeUploadedFile:
    def __init__(self, name, content: bytes):
        self.name = name
        self._content = content
    def getvalue(self):
        return self._content
    def read(self):
        return self._content

def make_service():
    repos = SqliteRepos()
    storage = LocalImageStorage()
    policy = MentorPolicy()
    return ArtConnectService(repos, storage, policy)

def test_full_flow_register_login_exhibition_upload_like_comment():
    s = make_service()
    repos: SqliteRepos = s.repos

    u = "it_user_" + uuid.uuid4().hex[:8]
    s.register(u, "pw123", "mentor")
    uid, role = s.login(u, "pw123")
    assert role == "mentor"

    s.create_exhibition("Integration Test Exhibition", "desc", uid)
    exhibitions = repos.list_exhibitions()
    assert exhibitions
    exh = exhibitions[0]

    before = len(repos.list_artworks(exh.id))
    uploaded = FakeUploadedFile("integration.png", b"x")
    s.upload_artwork(exh.id, uploaded, uid)
    artworks = repos.list_artworks(exh.id)
    assert len(artworks) == before + 1
    art = artworks[0]

    likes0 = repos.like_count(art.id)
    repos.toggle_like(uid, art.id)
    likes1 = repos.like_count(art.id)
    repos.toggle_like(uid, art.id)
    likes2 = repos.like_count(art.id)
    assert likes1 != likes0
    assert likes2 == likes0

    text = "Great artwork!"
    repos.add_comment(uid, art.id, text)
    comments = repos.list_comments(art.id)
    assert any(c[-1] == text for c in comments)
