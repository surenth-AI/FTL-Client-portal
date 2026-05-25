import re

_PASSWORD_RULES = (
    (lambda p: len(p) >= 12,          "Password must be at least 12 characters."),
    (lambda p: re.search(r'[A-Z]', p), "Password must contain at least one uppercase letter."),
    (lambda p: re.search(r'[a-z]', p), "Password must contain at least one lowercase letter."),
    (lambda p: re.search(r'\d', p),    "Password must contain at least one number."),
    (lambda p: re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/`~\\]', p),
                                       "Password must contain at least one special character."),
)

def validate_password_strength(password):
    """Returns (True, None) if valid, or (False, error_message) on first failure."""
    for check, message in _PASSWORD_RULES:
        if not check(password):
            return False, message
    return True, None
