import sqlite3
import time
from typing import Optional, Tuple


def now_ts() -> int:
    return int(time.time())


class DB:
    def __init__(self, path: str):
        self.path = path

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def init(self):
        con = self.conn()
        cur = con.cursor()

        # users + wallets
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
          tg_id INTEGER PRIMARY KEY,
          username TEXT,
          wallet TEXT,
          verified INTEGER DEFAULT 0,
          joined_at INTEGER
        )
        """)

        # points
        cur.execute("""
        CREATE TABLE IF NOT EXISTS points(
          tg_id INTEGER PRIMARY KEY,
          points INTEGER DEFAULT 0
        )
        """)

        # contest state
        cur.execute("""
        CREATE TABLE IF NOT EXISTS contest(
          id INTEGER PRIMARY KEY CHECK (id = 1),
          start_ts INTEGER,
          end_ts INTEGER,
          is_active INTEGER DEFAULT 0
        )
        """)
        cur.execute("INSERT OR IGNORE INTO contest(id, start_ts, end_ts, is_active) VALUES(1, NULL, NULL, 0)")

        # NEW: meme ownership registry
        cur.execute("""
        CREATE TABLE IF NOT EXISTS memes(
          chat_id INTEGER NOT NULL,
          meme_message_id INTEGER NOT NULL,
          owner_tg_id INTEGER NOT NULL,
          created_ts INTEGER NOT NULL,
          PRIMARY KEY(chat_id, meme_message_id)
        )
        """)

        # NEW: prevent double scoring of replies
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scored_replies(
          chat_id INTEGER NOT NULL,
          reply_message_id INTEGER NOT NULL,
          created_ts INTEGER NOT NULL,
          PRIMARY KEY(chat_id, reply_message_id)
        )
        """)

        # NEW: prevent reaction toggle farming
        # (1 point per user per meme)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scored_reactions(
          chat_id INTEGER NOT NULL,
          meme_message_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          created_ts INTEGER NOT NULL,
          PRIMARY KEY(chat_id, meme_message_id, user_id)
        )
        """)

        con.commit()
        con.close()

    # ---------- Users ----------
    def ensure_user(self, tg_id: int, username: str):
        con = self.conn()
        con.execute("INSERT OR IGNORE INTO users(tg_id, username, joined_at) VALUES(?,?,NULL)", (tg_id, username))
        con.execute("UPDATE users SET username=? WHERE tg_id=?", (username, tg_id))
        con.execute("INSERT OR IGNORE INTO points(tg_id, points) VALUES(?,0)", (tg_id,))
        con.commit()
        con.close()

    def get_user(self, tg_id: int):
        con = self.conn()
        row = con.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        con.close()
        return row

    def set_verified(self, tg_id: int, wallet: str, verified: int):
        con = self.conn()
        con.execute("UPDATE users SET wallet=?, verified=? WHERE tg_id=?", (wallet, verified, tg_id))
        con.commit()
        con.close()

    def mark_joined(self, tg_id: int):
        con = self.conn()
        con.execute("UPDATE users SET joined_at=? WHERE tg_id=? AND joined_at IS NULL", (now_ts(), tg_id))
        con.commit()
        con.close()

    def list_verified_users(self, only_joined: bool = True):
        con = self.conn()
        if only_joined:
            rows = con.execute("""
              SELECT tg_id, wallet, username
              FROM users
              WHERE verified=1 AND wallet IS NOT NULL AND joined_at IS NOT NULL
            """).fetchall()
        else:
            rows = con.execute("""
              SELECT tg_id, wallet, username
              FROM users
              WHERE verified=1 AND wallet IS NOT NULL
            """).fetchall()
        con.close()
        return rows

    def unverify_and_optionally_kick(self, tg_id: int, kick_from_contest: bool):
        con = self.conn()
        if kick_from_contest:
            con.execute("UPDATE users SET verified=0, joined_at=NULL WHERE tg_id=?", (tg_id,))
        else:
            con.execute("UPDATE users SET verified=0 WHERE tg_id=?", (tg_id,))
        con.commit()
        con.close()

    def find_user_by_username(self, username: str) -> Optional[int]:
        con = self.conn()
        row = con.execute("SELECT tg_id FROM users WHERE username=?", (username,)).fetchone()
        con.close()
        return int(row["tg_id"]) if row else None

    # ---------- Points ----------
    def add_points(self, tg_id: int, delta: int):
        con = self.conn()
        con.execute("UPDATE points SET points = COALESCE(points,0) + ? WHERE tg_id=?", (delta, tg_id))
        con.commit()
        con.close()

    def get_rank(self, tg_id: int) -> Optional[Tuple[int, int]]:
        con = self.conn()
        rows = con.execute("""
          SELECT u.tg_id, p.points, u.joined_at
          FROM points p
          JOIN users u ON u.tg_id = p.tg_id
          WHERE u.joined_at IS NOT NULL
          ORDER BY p.points DESC, u.joined_at ASC
        """).fetchall()
        con.close()
        for i, r in enumerate(rows, start=1):
            if int(r["tg_id"]) == tg_id:
                return (i, int(r["points"]))
        return None

    def top_leaderboard(self, limit: int = 10):
        con = self.conn()
        rows = con.execute("""
          SELECT u.username, u.tg_id, p.points
          FROM points p
          JOIN users u ON u.tg_id = p.tg_id
          WHERE u.joined_at IS NOT NULL
          ORDER BY p.points DESC, u.joined_at ASC
          LIMIT ?
        """, (limit,)).fetchall()
        con.close()
        return rows

    def top_n(self, n: int = 3):
        con = self.conn()
        rows = con.execute("""
          SELECT u.username, u.tg_id, p.points
          FROM points p
          JOIN users u ON u.tg_id = p.tg_id
          WHERE u.joined_at IS NOT NULL
          ORDER BY p.points DESC, u.joined_at ASC
          LIMIT ?
        """, (n,)).fetchall()
        con.close()
        return rows

    # ---------- Contest ----------
    def contest_status(self):
        con = self.conn()
        row = con.execute("SELECT start_ts, end_ts, is_active FROM contest WHERE id=1").fetchone()
        con.close()
        if not row:
            return (False, None, None)
        return (bool(row["is_active"]), row["start_ts"], row["end_ts"])

    def contest_is_live(self) -> bool:
        active, start_ts, end_ts = self.contest_status()
        if not active or not start_ts or not end_ts:
            return False
        t = now_ts()
        return start_ts <= t <= end_ts

    def set_contest_days(self, days: int):
        start = now_ts()
        end = start + days * 24 * 60 * 60
        con = self.conn()
        con.execute("UPDATE contest SET start_ts=?, end_ts=?, is_active=1 WHERE id=1", (start, end))
        con.commit()
        con.close()

    def end_contest(self):
        con = self.conn()
        con.execute("UPDATE contest SET is_active=0 WHERE id=1")
        con.commit()
        con.close()

    # ---------- Meme scoring storage ----------
    def insert_meme(self, chat_id: int, meme_message_id: int, owner_tg_id: int) -> bool:
        con = self.conn()
        try:
            con.execute(
                "INSERT INTO memes(chat_id, meme_message_id, owner_tg_id, created_ts) VALUES(?,?,?,?)",
                (chat_id, meme_message_id, owner_tg_id, now_ts())
            )
            con.commit()
            return True
        except Exception:
            return False
        finally:
            con.close()

    def get_meme_owner(self, chat_id: int, meme_message_id: int) -> Optional[int]:
        con = self.conn()
        row = con.execute(
            "SELECT owner_tg_id FROM memes WHERE chat_id=? AND meme_message_id=?",
            (chat_id, meme_message_id)
        ).fetchone()
        con.close()
        return int(row["owner_tg_id"]) if row else None

    def mark_reply_scored(self, chat_id: int, reply_message_id: int) -> bool:
        con = self.conn()
        try:
            con.execute(
                "INSERT INTO scored_replies(chat_id, reply_message_id, created_ts) VALUES(?,?,?)",
                (chat_id, reply_message_id, now_ts())
            )
            con.commit()
            return True
        except Exception:
            return False
        finally:
            con.close()

    def mark_reaction_scored(self, chat_id: int, meme_message_id: int, user_id: int) -> bool:
        con = self.conn()
        try:
            con.execute(
                "INSERT INTO scored_reactions(chat_id, meme_message_id, user_id, created_ts) VALUES(?,?,?,?)",
                (chat_id, meme_message_id, user_id, now_ts())
            )
            con.commit()
            return True
        except Exception:
            return False
        finally:
            con.close()
