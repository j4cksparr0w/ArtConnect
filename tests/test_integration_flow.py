from core.repositories import SqliteRepos
from core.services import ArtConnectService
from core.storage import LocalImageStorage
from core.policies import MentorPolicy


class FakeUploadedFile:
    def __init__(self, name: str, content: bytes) -> None:
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content

    def read(self) -> bytes:
        return self._content


def _make_service() -> ArtConnectService:
    repos = SqliteRepos()
    storage = LocalImageStorage()
    policy = MentorPolicy()
    return ArtConnectService(repos, storage, policy)


def test_full_flow_register_login_exhibition_upload_like_comment():
    service = _make_service()
    repos: SqliteRepos = service.repos  # type: ignore

    username = "it_user_integration"
    password = "secret123"
    role = "mentor"

    try:
        service.register(username, password, role)
    except Exception:
        pass

    login_result = service.login(username, password)
    assert login_result is not None
    user_id, logged_role = login_result
    assert logged_role == role

    theme = "Integration Test Exhibition"
    description = "Exhibition created by integration test."

    service.create_exhibition(theme, description, user_id)

    exhibitions = repos.list_exhibitions()
    matching = [e for e in exhibitions if e.theme == theme and e.description == description]
    assert matching

    exhibition = matching[-1]

    before_artworks = len(repos.list_artworks(exhibition.id))

    uploaded = FakeUploadedFile("integration.png", b"integration-bytes")
    service.upload_artwork(exhibition.id, uploaded, user_id)

    artworks_after = repos.list_artworks(exhibition.id)
    assert len(artworks_after) == before_artworks + 1

    artwork = artworks_after[-1]

    likes_initial = repos.like_count(artwork.id)

    repos.toggle_like(user_id, artwork.id)
    likes_after_first = repos.like_count(artwork.id)

    repos.toggle_like(user_id, artwork.id)
    likes_after_second = repos.like_count(artwork.id)

    assert likes_after_first != likes_initial
    assert likes_after_second == likes_initial

    comment_text = "Great artwork!"
    repos.add_comment(user_id, artwork.id, comment_text)

    comments = repos.list_comments(artwork.id)
    assert any(text == comment_text for (_username, text) in comments)
