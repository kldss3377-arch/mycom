"""회원가입 / 로그인 (PBKDF2 비밀번호 해시)."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3

from database import get_user, insert_user

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters)).hex()
    return hmac.compare_digest(check, digest)


def validate_registration(userid, username, password, password_confirm, email) -> list[str]:
    errors = []
    if not re.fullmatch(r"[A-Za-z0-9_]{4,20}", userid or ""):
        errors.append("아이디는 영문/숫자/밑줄(_) 4~20자로 입력해 주세요.")
    if not (username or "").strip():
        errors.append("사용자 이름을 입력해 주세요.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""):
        errors.append("올바른 이메일 형식이 아닙니다.")
    if len(password or "") < 6:
        errors.append("비밀번호는 6자 이상이어야 합니다.")
    if password != password_confirm:
        errors.append("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
    return errors


def create_user(userid, username, password, email) -> tuple[bool, str]:
    if get_user(userid):
        return False, "이미 사용 중인 아이디입니다."
    try:
        insert_user(userid, username.strip(), hash_password(password), email.strip())
    except sqlite3.IntegrityError:
        return False, "이미 사용 중인 아이디입니다."
    return True, "사용자 등록이 완료되었습니다. 로그인해 주세요."


def authenticate_user(userid, password) -> dict | None:
    user = get_user((userid or "").strip())
    if user and verify_password(password or "", user["password"]):
        return user
    return None
