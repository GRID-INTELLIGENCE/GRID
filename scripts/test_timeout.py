import os
import sqlite3
import time

# Add the directory containing 'mcp' to path so we can verify the server logic if needed,
# but here we will just test the logic concept since we can't easily import the full server without mcp package potentially.
# However, we can use the exact logic snippet I wrote to test it in isolation.


def test_sqlite_progress_handler():
    print("Testing SQLite progress handler for timeout...")

    db_path = "test_timeout.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    # Create a table with many rows to query
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
    print("Seeding data...")
    conn.executemany("INSERT INTO test (data) VALUES (?)", [("x" * 100,) for _ in range(10000)])
    conn.commit()

    # The logic from server.py replacement:
    query_start_time = time.time()
    query_timeout = 0.1  # Set a very short timeout for testing

    def progress_handler():
        if time.time() - query_start_time > query_timeout:
            return 1  # Non-zero output interrupts
        return 0

    conn.set_progress_handler(progress_handler, 100)

    try:
        print("Running slow query...")
        # A cartesian product to ensure it takes time
        conn.execute("SELECT count(*) FROM test a, test b")
        print("Query finished (unexpected for timeout test)")
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            print("SUCCESS: Query time out verified (interrupted).")
        else:
            print(f"FAILED: OperationalError but not interrupted: {e}")
    except Exception as e:
        print(f"FAILED: Unexpected exception: {e}")
    finally:
        conn.close()
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    test_sqlite_progress_handler()
