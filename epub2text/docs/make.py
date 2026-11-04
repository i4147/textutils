import os
import shutil
import subprocess
import sys


def main() -> int:
    sphinx_build = "sphinx-build"
    build_dir = os.path.join("docs", "build")
    source_dir = "docs"

    if len(sys.argv) < 2:
        target = "html"
    else:
        target = sys.argv[1]

    if target == "clean":
        if os.path.exists(build_dir):
            print(f"Cleaning {build_dir}...")
            shutil.rmtree(build_dir)
        return 0

    if target == "help":
        print(__doc__)
        return 0

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    valid_targets = {
        "html",
        "dirhtml",
        "latex",
        "latexpdf",
        "text",
        "man",
        "changes",
        "linkcheck",
        "doctest",
        "all",
    }

    if target not in valid_targets:
        print(f"Unknown target: {target}")
        print("Use 'help' target for help")
        return 1

    if target == "all":
        for fmt in ["html", "dirhtml", "latex"]:
            cmd = [sphinx_build, "-b", fmt, source_dir, os.path.join(build_dir, fmt)]
            print(f"Building {fmt} documentation...")
            subprocess.run(cmd, check=True)
    else:
        cmd = [sphinx_build, "-b", target, source_dir, os.path.join(build_dir, target)]
        print(f"Building {target} documentation...")
        subprocess.run(cmd, check=True)

    print(f"Build finished. Documentation is in {os.path.join(build_dir, target)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
