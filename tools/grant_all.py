"""
Unlock everything for one account: every level of every course marked
complete, every secret achievement awarded. For demo and test accounts.

    python3 tools/grant_all.py testing            # uses academy.db (or ACADEMY_DB)
    python3 tools/grant_all.py testing --revoke   # takes it all away again

Times are left empty, so the account never appears on the level-time
leaderboards because of this script.
"""

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import progress  # noqa: E402
from achievements import ACHIEVEMENTS  # noqa: E402
from curriculum import COURSES  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    username = sys.argv[1]
    revoke = "--revoke" in sys.argv
    path = os.getenv("ACADEMY_DB", os.path.join(ROOT, "academy.db"))

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    progress.migrate(conn)

    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if user is None:
        print("No account called %r in %s" % (username, path))
        return 1

    user_id = user["id"]
    levels = 0

    if revoke:
        conn.execute("DELETE FROM level_progress WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM level_checkpoints WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM achievements WHERE user_id = ?", (user_id,))
        conn.commit()
        print("Revoked every level and achievement for %s." % username)
        return 0

    for course in COURSES.values():
        for lvl in course["levels"]:
            progress.record_completion(conn, user_id, course["slug"], lvl["number"], None)
            levels += 1

    for achievement in ACHIEVEMENTS:
        progress.award_achievement(conn, user_id, achievement["key"])

    conn.commit()
    conn.close()

    print("%s: %d levels completed, %d achievements awarded (%s)." % (username, levels, len(ACHIEVEMENTS), path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
