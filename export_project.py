import os

OUTPUT_FILE = "project_code_dump.txt"
# export_project.py
IGNORE_DIRS = {'.git', '.idea', 'venv', '.venv', '__pycache__', 'assets', '.pytest_cache'}
INCLUDE_EXTS = {'.py', '.ui', '.xml', '.css', '.html', '.json', '.sql'}

def generate_dump():
    project_root = os.getcwd()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("=== PROJECT STRUCTURE ===\n")
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            level = root.replace(project_root, '').count(os.sep)
            out.write(f"{' ' * 4 * level}{os.path.basename(root)}/\n")
            for f in files:
                out.write(f"{' ' * 4 * (level + 1)}{f}\n")

        out.write("\n\n=== FILE CONTENTS ===\n")
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if any(file.endswith(ext) for ext in INCLUDE_EXTS):
                    filepath = os.path.join(root, file)
                    if file == "export_project.py" or file == OUTPUT_FILE: continue
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            out.write(f"\n{'='*50}\nFILE: {os.path.relpath(filepath, project_root)}\n{'='*50}\n{f.read()}\n")
                    except Exception as e:
                        out.write(f"\n[ERROR READING {file}: {e}]\n")
    print(f"Done! Upload '{OUTPUT_FILE}' here.")

if __name__ == "__main__":
    generate_dump()