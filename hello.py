"""Tiny app used in the branching demo."""


def refresh_token(user):
    if not user:
        return None
    # Bug: never actually rotates the token — same value returned forever.
    return user.get("token")


def greet(user):
    token = refresh_token(user)
    return f"hello {user['name']} ({'no token' if not token else token})"
