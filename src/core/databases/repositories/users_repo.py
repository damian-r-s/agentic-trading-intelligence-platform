from src.core.databases.database import get_conn
from src.core.encryption import decrypt_secret, encrypt_secret


def create_user(username, password_hash) -> int:
    sql = """
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s)
        RETURNING id
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (username, password_hash))
            return cur.fetchone()[0]


def get_user_by_username(username):
    sql = "SELECT id, username, password_hash FROM users WHERE username = %s"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
            if row is None:
                return None
            return {"id": row[0], "username": row[1], "password_hash": row[2]}


def list_user_ids() -> list[int]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users ORDER BY id")
            return [row[0] for row in cur.fetchall()]


def get_binance_credentials(user_id) -> tuple[str, str] | None:
    sql = """
        SELECT binance_api_key_enc, binance_api_secret_enc
        FROM users WHERE id = %s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            if row is None or row[0] is None or row[1] is None:
                return None
            return decrypt_secret(row[0]), decrypt_secret(row[1])


def set_binance_credentials(user_id, api_key, api_secret) -> None:
    sql = """
        UPDATE users
        SET binance_api_key_enc = %s, binance_api_secret_enc = %s
        WHERE id = %s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (encrypt_secret(api_key), encrypt_secret(api_secret), user_id))
