import shutil
import os

source_dir = r"c:\Users\HP\Downloads\FirstAid-AI-Chatbot (3)\FirstAid-AI-Chatbot"
target_dir = r"c:\Users\HP\Downloads\hi"

os.makedirs(target_dir, exist_ok=True)

# Copy updated folders
for folder in ["src", "public", "data"]:
    s = os.path.join(source_dir, folder)
    d = os.path.join(target_dir, folder)
    if os.path.exists(s):
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "books"))
        print(f"Updated folder: {folder}")

# Copy updated root files
files_to_copy = ["app.py", "config.py", "requirements.txt", "README.md", ".env.example"]
for f in files_to_copy:
    src_file = os.path.join(source_dir, f)
    dst_file = os.path.join(target_dir, f)
    if os.path.exists(src_file):
        shutil.copy2(src_file, dst_file)
        print(f"Updated file: {f}")

print("REFRESH_DONE")

