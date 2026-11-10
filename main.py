import os
import json
import zipfile
import shutil
import hashlib
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
MODS = os.path.join(ROOT, "mods")
LOGS = os.path.join(ROOT, "logs")
LANGS = os.path.join(ROOT, "translations")

for folder in [MODS, LOGS, LANGS]:
    os.makedirs(folder, exist_ok=True)

DATABASE = os.path.join(ROOT, "database.json")

def load_db():
    if not os.path.exists(DATABASE):
        return {"mods": []}
    with open(DATABASE, encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DATABASE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log(message):
    with open(os.path.join(LOGS, "activity.log"), "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")

def inspect_mod(path):
    result = {
        "filename": os.path.basename(path),
        "extension": os.path.splitext(path)[1].lower(),
        "size": os.path.getsize(path),
        "sha256": "",
        "archive": False,
        "files": [],
        "status": "UNKNOWN"
    }

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)

    result["sha256"] = h.hexdigest()

    if zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path) as z:
                result["archive"] = True
                result["files"] = z.namelist()[:100]
                result["status"] = "ARCHIVE_READABLE"
        except Exception as e:
            result["status"] = "ARCHIVE_ERROR: " + str(e)

    return result

def import_mod(path):
    if not os.path.isfile(path):
        print("File not found!")
        return

    ext = os.path.splitext(path)[1].lower()

    if ext not in [".hmod", ".hnmod"]:
        print("Unsupported extension!")
        return

    name = os.path.basename(path)
    destination = os.path.join(MODS, name)

    if os.path.exists(destination):
        print("Mod already exists!")
        return

    shutil.copy2(path, destination)

    info = inspect_mod(destination)
    info["enabled"] = False
    info["imported"] = datetime.now().isoformat()

    db = load_db()
    db["mods"].append(info)
    save_db(db)

    log("Imported: " + name)
    print("Imported successfully:", name)
    print("Inspection:", info["status"])

def list_mods():
    db = load_db()

    if not db["mods"]:
        print("No mods installed.")
        return

    for i, mod in enumerate(db["mods"]):
        state = "ON" if mod["enabled"] else "OFF"
        print(f'{i+1}. {mod["filename"]} | {state} | {mod["extension"]}')

def toggle_mod(index):
    db = load_db()

    if index < 0 or index >= len(db["mods"]):
        print("Invalid number!")
        return

    mod = db["mods"][index]
    mod["enabled"] = not mod["enabled"]

    save_db(db)
    log("Toggled: " + mod["filename"])

    print("Enabled" if mod["enabled"] else "Disabled")

def translations():
    language = input("Language (ar/en): ").strip().lower()

    path = os.path.join(LANGS, language + ".json")

    if not os.path.exists(path):
        print("Language not found!")
        return

    with open(path, encoding="utf-8") as f:
        words = json.load(f)

    for key, value in words.items():
        print(key, "=", value)

def inspect_all():
    db = load_db()

    for mod in db["mods"]:
        path = os.path.join(MODS, mod["filename"])
        if os.path.isfile(path):
            print(json.dumps(inspect_mod(path), indent=2, ensure_ascii=False))

def menu():
    while True:
        print("""
================================
       HORIZON MOD MANAGER
================================
1. Import HMOD / HNMOD
2. List Mods
3. Enable / Disable Mod
4. Inspect Mods
5. Translation System
0. Exit
================================
""")

        choice = input("Select: ").strip()

        if choice == "1":
            path = input("Mod file path: ").strip()
            import_mod(path)

        elif choice == "2":
            list_mods()

        elif choice == "3":
            list_mods()
            try:
                n = int(input("Mod number: ")) - 1
                toggle_mod(n)
            except ValueError:
                print("Invalid input!")

        elif choice == "4":
            inspect_all()

        elif choice == "5":
            translations()

        elif choice == "0":
            break

        else:
            print("Invalid choice!")

if __name__ == "__main__":
    menu()
