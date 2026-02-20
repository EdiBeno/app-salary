import time
import os

WATCHED_FILES = ["database.py", "models.py", "app.py"]

last_modified = {f: os.path.getmtime(f) for f in WATCHED_FILES}

print("Auto‑migrate watcher running...")

while True:
    for f in WATCHED_FILES:
        current = os.path.getmtime(f)
        if current != last_modified[f]:
            print(f"\nDetected change in {f} → running migration...")
            os.system("flask db migrate -m 'auto update'")
            os.system("flask db upgrade")
            last_modified[f] = current
    time.sleep(1)
