from core.policies import StudentPolicy, MentorPolicy

def test_student_cannot_upload():
    policy = StudentPolicy()
    assert policy.can_upload() is False

def test_mentor_can_upload():
    policy = MentorPolicy()
    assert policy.can_upload() is True
