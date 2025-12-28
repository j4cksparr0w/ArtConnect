from typing import Protocol

class RolePolicy(Protocol):
    def can_upload(self) -> bool: ...

class StudentPolicy:
    def can_upload(self) -> bool:
        return False

class MentorPolicy:
    def can_upload(self) -> bool:
        return True
