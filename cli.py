import argparse
import sys

from reelsaver import db
from reelsaver.ingest import run_ingest
from reelsaver.sources.instagram_dm import InstagramDMSource


def cmd_run() -> int:
    conn = db.connect()
    try:
        db.init_db(conn)
        run_ingest(InstagramDMSource(), conn)
    except Exception as e:
        print(f"Run failed, nothing saved: {type(e).__name__}: {e}")
        return 1
    finally:
        conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="reelrecall")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="fetch new reels from Instagram and save them")
    args = parser.parse_args()

    if args.command == "run":
        return cmd_run()
    return 0


if __name__ == "__main__":
    sys.exit(main())