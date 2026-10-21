"""SQLite3 데이터베이스 모듈 (mycom.db)."""
from __future__ import annotations

import csv
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mycom.db"
LEGACY_CSV = BASE_DIR / "data" / "data.csv"
KST = ZoneInfo("Asia/Seoul")


def now_str() -> str:
    """현재 한국 시간 문자열 (YYYY-MM-DD HH:MM:SS)."""
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        # mycom.sql 의 user_table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_table (
                id_num     INTEGER PRIMARY KEY AUTOINCREMENT,  -- 관리번호
                userid     TEXT    NOT NULL UNIQUE,            -- 로그인 아이디
                username   TEXT    NOT NULL,                   -- 이름
                password   TEXT    NOT NULL,                   -- 해시된 비밀번호
                email      TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            )
            """
        )
        # mycom.sql 의 survey_table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS "survey_table" (
                "id_num"     INTEGER NOT NULL,
                "user_id"    TEXT,
                "q1" INTEGER, "q2" INTEGER, "q3" INTEGER, "q4" INTEGER, "q5" INTEGER,
                "q6" INTEGER, "q7" INTEGER, "q8" INTEGER, "q9" INTEGER, "q10" INTEGER,
                "created_at" TEXT,
                PRIMARY KEY("id_num" AUTOINCREMENT)
            )
            """
        )
        # 홈 화면 입력 폼(Name/Age/Address/Phone) 저장용
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_table (
                id_num     INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                name       TEXT    NOT NULL,
                age        INTEGER NOT NULL,
                address    TEXT    NOT NULL,
                phone      TEXT    NOT NULL,
                created_at TEXT    NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user_table(id_num)
            )
            """
        )
        # 첨부 CSV 레거시 데이터 보관용
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS legacy_profile_table (
                id_num  INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT,
                age     TEXT,
                address TEXT,
                phone   TEXT
            )
            """
        )


# ---------------------------------------------------------------- user
def get_user(userid: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM user_table WHERE userid = ?", (userid,)).fetchone()
    return dict(row) if row else None


def insert_user(userid: str, username: str, password_hash: str, email: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_table (userid, username, password, email, created_at) VALUES (?, ?, ?, ?, ?)",
            (userid, username, password_hash, email, now_str()),
        )


# ---------------------------------------------------------------- profile
def add_profile(user_id: int, name: str, age: int, address: str, phone: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO profile_table (user_id, name, age, address, phone, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name.strip(), age, address.strip(), phone.strip(), now_str()),
        )


def get_user_profiles(user_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id_num AS 번호, name AS Name, age AS Age, address AS Address, phone AS Phone, created_at AS 등록일시 "
            "FROM profile_table WHERE user_id = ? ORDER BY id_num DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- legacy csv
def migrate_legacy_csv() -> None:
    """data/data.csv 가 있으면 legacy_profile_table 로 1회만 옮긴다."""
    if not LEGACY_CSV.exists():
        return
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM legacy_profile_table").fetchone()[0] > 0:
            return
        for enc in ("utf-8-sig", "cp949"):
            try:
                with LEGACY_CSV.open(encoding=enc, newline="") as f:
                    rows = list(csv.DictReader(f))
                break
            except UnicodeDecodeError:
                rows = []
        for r in rows:
            low = {str(k).strip().lower(): v for k, v in r.items() if k}
            conn.execute(
                "INSERT INTO legacy_profile_table (name, age, address, phone) VALUES (?, ?, ?, ?)",
                (low.get("name"), low.get("age"), low.get("address"), low.get("phone")),
            )


def get_legacy_profiles() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT name AS Name, age AS Age, address AS Address, phone AS Phone FROM legacy_profile_table"
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- survey
QUESTION_COLS = [f"q{i}" for i in range(1, 11)]


def add_survey(user_id: str, answers: list[int]) -> str:
    created_at = now_str()
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO survey_table (user_id, {', '.join(QUESTION_COLS)}, created_at) "
            f"VALUES (?, {', '.join('?' * 10)}, ?)",
            (user_id, *answers, created_at),
        )
    return created_at


def get_surveys() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM survey_table ORDER BY id_num").fetchall()
    return [dict(r) for r in rows]


def get_user_surveys(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM survey_table WHERE user_id = ? ORDER BY id_num DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]
