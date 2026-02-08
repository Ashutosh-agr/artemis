from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def _sha256(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    return pwd_context.hash(_sha256(password))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_sha256(plain_password), hashed_password)
