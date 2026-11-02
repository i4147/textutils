from setuptools import setup

packages = ["textcheck", "textcheck.lib"]
package_data = {"": ["*"]}
install_requires = ["rich", "spacy==2.3.7", "spacy_hunspell>=0.1.0,<0.2.0", "stackprinter", "typer"]
entry_points = {"console_scripts": ["textcheck = textcheck.main:app"]}
setup_kwargs = {
    "name": "textcheck",
    "version": "0.2.1",
    "description": "Check text files for issues.",
    "long_description": "# textcheck\n\nRun text checks on files from the command line.\n\n```\nв”Ҹв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”ів”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”ів”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”“\nв”ғ Word    в”ғ Alternatives                                    в”ғ Context                       в”ғ\nв”Ўв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв•Үв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв•Үв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”Ғв”©\nв”Ӯ speling в”Ӯ spieling, spelling, spewing, peeling, splinting в”Ӯ should be checked for speling в”Ӯ\nв””в”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”ҙв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”ҙв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”Җв”ҳ\n```\n## Installation\n\nHunspell dictionary files `en_US.dic` and `en_US.aff` need to be placed in `/usr/share/hunspell` directory.\n\n## CLI usage\n\n### `spellcheck`\n\nRun spellcheck for a set of files\n\n**Usage**:\n\n```console\n$ textcheck spellcheck [OPTIONS] FILES...\n```\n\n**Arguments**:\n\n* `FILES...`: [required]",
    "author": "Petr Stribny",
    "author_email": "petr@stribny.name",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/stribny/textcheck",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.9,<4.0",
}
setup(**setup_kwargs)
