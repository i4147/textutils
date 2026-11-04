from pathlib import Path
import os


def main():
    project = Path("princetext_project")

    project.mkdir(exist_ok=True)

    (project / "README.md").write_text("# My Project")
    (project / "app.py").write_text('print("Hello World")')

    os.system("python3 -m venv princetext_project/venv")

    print("Project created successfully!")
