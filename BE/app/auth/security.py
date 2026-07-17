from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """Hash a password using pwdlib."""
    return password_hasher.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password using pwdlib."""
    return password_hasher.verify(password, hashed_password)
