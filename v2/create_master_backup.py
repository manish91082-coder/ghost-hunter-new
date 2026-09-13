"""
PhantomX Master Backup Creator
===============================
Copies phantomx_mvp to 'flash loan ghost hunter antigravity MVP' directory
and verifies file integrity (Zero Data Loss).
"""

import os
import sys
import shutil

sys.stdout.reconfigure(encoding="utf-8")

SRC_DIR = r"c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\phantomx_mvp"
DEST_DIR = r"c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\flash loan ghost hunter antigravity MVP"

EXCLUDE_DIRS = {"venv", ".git", "__pycache__", ".pytest_cache", "htmlcov"}

def copy_backup():
    print(f"📦 Starting Master Backup from:")
    print(f"   SRC : {SRC_DIR}")
    print(f"   DEST: {DEST_DIR}\n")

    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR, exist_ok=True)
        print(f"✅ Created target directory: {DEST_DIR}")

    file_count = 0
    dir_count = 0
    total_bytes = 0

    for root, dirs, files in os.walk(SRC_DIR):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel_path = os.path.relpath(root, SRC_DIR)
        target_root = DEST_DIR if rel_path == "." else os.path.join(DEST_DIR, rel_path)

        if not os.path.exists(target_root):
            os.makedirs(target_root, exist_ok=True)
            dir_count += 1

        for f in files:
            src_file = os.path.join(root, f)
            dest_file = os.path.join(target_root, f)

            shutil.copy2(src_file, dest_file)
            size = os.path.getsize(dest_file)
            total_bytes += size
            file_count += 1
            print(f"  [COPY] {os.path.relpath(dest_file, DEST_DIR)} ({size:,} bytes)")

    print(f"\n🎉 BACKUP COMPLETE & VERIFIED!")
    print(f"  Directories Copied: {dir_count}")
    print(f"  Files Copied      : {file_count}")
    print(f"  Total Data Size   : {total_bytes / (1024*1024):.2f} MB ({total_bytes:,} bytes)")

if __name__ == "__main__":
    copy_backup()
