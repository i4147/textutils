extract functions & classes from these pkgs &
use them to build a textutils library 
for linux env (drop any windows & mac support)
- drop any pytjon2 support & compat code
- refactor codes to modern py3.12+
- migrate from stdlib logging to loguru
- use pathlib for fs traverse (instead of os.path)
- use mp.pool.imap_unordered with 4 workets for parallel processinb
- refactor argparse & ckick to typer
- return fully refactored & type-annotated & documented code (save in result dir)

save the helper scripts (bash, python, ...) thst you used during this session under arena folder in root of connected repo
