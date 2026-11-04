import datetime
from hashlib import sha256
import hashlib
import importlib.resources
import os
from collections.abc import Generator
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
import platform
import re
import shutil
import socketserver
import socket
import subprocess
import time as time
import logging
import logging.handlers
import psutil
import typing as t
from . import types as pt
from lxml import etree as ET
from lxml.etree import _ElementTree, _Element

try:
    import pelican.settings
except ImportError:
    pass
from typing import Any, cast, List, Optional

from . import core, constants, resources, VERSION

log = logging.getLogger("ptxlogger")


@contextmanager
def working_directory(path: Path) -> Generator:
    current_directory = Path.cwd()
    os.chdir(path)
    log.debug(f"Now working in directory {path}")
    try:
        yield
    finally:
        os.chdir(current_directory)
        log.debug(f"Successfully changed directory back to {current_directory}")


def manage_directories(
    output_dir: Path,
    external_abs: Optional[Path] = None,
    generated_abs: Optional[Path] = None,
) -> None:
    if external_abs is not None:
        external_dir = os.path.join(output_dir, "external")
        shutil.copytree(external_abs, external_dir, dirs_exist_ok=True)

    if generated_abs is not None:
        generated_dir = os.path.join(output_dir, "generated")
        shutil.copytree(
            generated_abs,
            generated_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.pkl"),
        )


def project_path(dirpath: Optional[Path] = None) -> Optional[Path]:
    if dirpath is None:
        dirpath = Path().resolve()
    if (dirpath / "project.ptx").is_file():
        return dirpath
    if dirpath.parent == dirpath:
        return None
    else:
        return project_path(dirpath=dirpath.parent)


def project_path_found(dirpath: Optional[Path] = None) -> Path:
    pp = project_path(dirpath)
    assert pp is not None, "Invalid project path"
    return pp


def ensure_default_project_manifest() -> None:
    template_manifest = resources.resource_base_path() / "templates" / "project.ptx"
    user_project_manifest = resources.resource_base_path().parent / "project.ptx"
    log.debug(f"Checking for user's default project.ptx manifest at {user_project_manifest}")
    if not user_project_manifest.exists():
        shutil.copy(template_manifest, user_project_manifest)
        log.debug("Copied default project.ptx manifest to user's default project.ptx manifest.")


def project_xml(dirpath: t.Optional[Path] = None) -> _ElementTree:
    if dirpath is None:
        dirpath = Path.cwd()
    pp = project_path(dirpath)
    if pp is None:
        project_manifest = resources.resource_base_path() / "templates" / "project.ptx"
    else:
        project_manifest = pp / "project.ptx"
    return ET.parse(project_manifest)


def requirements_version(dirpath: Optional[Path] = None) -> Optional[str]:
    if dirpath is None:
        dirpath = Path.cwd()
    pp = project_path(dirpath)
    if pp is None:
        return None
    try:
        with open(pp / "requirements.txt", "r") as f:
            regex = r"\s*pretext(book)?(\[.*\])?\s*==\s*(?P<version>[\d\.]+)\s*"
            for line in f.readlines():
                match = re.match(regex, line)
                if match:
                    return match.group("version")
    except Exception as e:
        log.debug("Could not read `requirements.txt`:")
        log.debug(e)
    return None


def project_xml_string(dirpath: Optional[Path] = None) -> str:
    if dirpath is None:
        dirpath = Path.cwd()
    return ET.tostring(project_xml(dirpath), encoding="unicode")


def home_path() -> Path:
    return Path.home() / ".ptx"


def hash_path(project_path: Path) -> str:
    return sha256(str(project_path).encode("utf-8")).hexdigest()[:10]


def target_xml(alias: t.Optional[str] = None, dirpath: t.Optional[Path] = None) -> Optional[_Element]:
    if dirpath is None:
        dirpath = Path.cwd()
    if alias is None:
        return project_xml().find("targets/target")
    xpath = f'targets/target[@name="{alias}"]'
    _matches = project_xml().xpath(xpath)
    matches = cast(List[_Element], _matches)
    if len(matches) == 0:
        log.info(f"No targets with alias {alias} found in project manifest file project.ptx.")
        return None
    return matches[0]


def xml_syntax_is_valid(xmlfile: Path, root_tag: str = "pretext") -> bool:
    try:
        source_xml = ET.parse(xmlfile)
        source_xml.xinclude()
        log.debug("XML syntax appears well formed.")
        if source_xml.getroot().tag != root_tag:
            log.error(
                f"The file {xmlfile} does not have `{root_tag}` element as its root element.  Did you use a subfile as your source?  Check the project manifest (project.ptx)."
            )
            return False
    except IOError:
        raise IOError(f"The file {xmlfile} does not exist")
    except ET.XMLSyntaxError as err:
        log.error("XML Syntax Error caused build to fail:")
        log.error(str(err.error_log))
        return False
    except ET.XIncludeError as err:
        log.error("XInclude Error caused build to fail:")
        log.error(str(err.error_log))
        return False
    return True


def warn_on_schema_errors(etree: _Element, log_dir: Path) -> Optional[bool]:
    schema_file = schema_path()
    log.debug(f"Validating PreTeXt source against schema {schema_file}")
    log_dir.mkdir(parents=True, exist_ok=True)
    assembled_source = log_dir / "schema-assembled-source.xml"
    error_log = log_dir / "schema-errors.log"
    etree.getroottree().write(str(assembled_source), encoding="utf-8", xml_declaration=True)

    def _discard() -> None:
        assembled_source.unlink(missing_ok=True)
        error_log.unlink(missing_ok=True)

    result = validate_with_jing(assembled_source, schema_file)
    if result is None:
        log.debug(
            "No jing executable available, so the source was not checked against "
            "the schema. Install jing (or set it in executables.ptx) to have "
            "builds report schema errors."
        )
        _discard()
        return None

    is_valid, output = result
    if is_valid:
        log.debug("PreTeXt source passed schema validation.")
        _discard()
        return True

    error_log.write_text(output, encoding="utf-8")
    message_count = len([line for line in output.splitlines() if line.strip()])
    log.warning(
        f"PreTeXt source did not pass schema validation ({message_count} messages); "
        "unexpected output may result. Continuing anyway."
    )
    log.warning(f"  Messages: {error_log}")
    log.warning(f"  Line numbers refer to the assembled source: {assembled_source}")
    log.warning("  Run `pretext validate` for a report that names the source files.")
    return False


def _jing_command() -> Optional[List[str]]:
    try:
        return core.get_executable_cmd("jing")
    except (KeyError, TypeError, OSError) as e:
        log.debug(f"Could not use a configured jing command: {e}")
    jing_executable = shutil.which("jing")
    return [jing_executable] if jing_executable is not None else None


def salve_shim_command() -> Optional[List[str]]:
    node_cmd = shutil.which("node")
    if node_cmd is None:
        log.warning("The salve validator needs node, which could not be found.")
        return None

    shim_dir = resources.resource_base_path() / "salve"
    shim = shim_dir / "ptx-jing-shim.mjs"

    if not (shim_dir / "node_modules").exists():
        npm_cmd = shutil.which("npm")
        if npm_cmd is None:
            log.warning("The salve validator needs npm to install itself on first use.")
            return None
        log.info(f"Installing the salve validator into {shim_dir} (first use only).")
        shim_dir.mkdir(parents=True, exist_ok=True)
        for name in ("ptx-jing-shim.mjs", "package.json"):
            with importlib.resources.path("pretext.resources.salve", name) as src:
                shutil.copy2(src, shim_dir / name)
        try:
            result = subprocess.run([npm_cmd, "install"], cwd=shim_dir, capture_output=True, text=True)
        except OSError as e:
            log.warning(f"Could not install the salve validator: {e}")
            return None
        if result.returncode != 0:
            log.warning("Could not install the salve validator with npm:")
            log.warning(result.stderr.strip())
            return None

    if not shim.exists():
        log.warning(f"The salve validator is missing from {shim_dir}.")
        return None
    return [node_cmd, str(shim)]


def validate_with_jing(source_file: Path, schema_file: Path) -> Optional[tuple[bool, str]]:
    jing_command = _jing_command()
    if jing_command is None:
        return None

    try:
        result = subprocess.run(
            jing_command + [str(schema_file), str(source_file)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    output = "\n".join(chunk for chunk in [result.stdout.strip(), result.stderr.strip()] if chunk)
    if result.returncode > 1:
        log.debug(f"The jing program failed (code {result.returncode}): {output}")
        return None
    return result.returncode == 0, output


def schema_path(dev: bool = False) -> Path:
    schema_name = "pretext-dev.rng" if dev else "pretext.rng"
    return resources.resource_base_path() / "core" / "schema" / schema_name


def binding_for_access(access: t.Literal["public", "private"] = "private") -> str:
    if access == "private":
        return "localhost"
    return "0.0.0.0"


def url_for_access(access: t.Literal["public", "private"] = "private", port: int = 8000) -> str:
    if access == "private":
        if os.environ.get("CODESPACES") == "true":
            return f"https://{os.environ.get('CODESPACE_NAME')}-{port}.{os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')}"
        else:
            return f"http://localhost:{port}"
    return f"http://{socket.gethostbyname(socket.gethostname())}:{port}"


def serve_forever(
    base_dir: Path,
    access: t.Literal["public", "private"] = "private",
    port: int = 8128,
) -> None:
    binding = binding_for_access(access)

    class RequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any):
            super().__init__(*args, directory=base_dir.as_posix(), **kwargs)

        """HTTP request handler with no caching"""

        def end_headers(self) -> None:
            self.send_my_headers()
            SimpleHTTPRequestHandler.end_headers(self)

        def send_my_headers(self) -> None:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

    class TCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    looking_for_port = True
    while looking_for_port:
        try:
            with TCPServer((binding, port), RequestHandler) as httpd:
                looking_for_port = False
                httpd.serve_forever()
        except OSError:
            log.warning(f"Port {port} could not be used.")
            port += 1
            log.warning(f"Trying port {port} instead.\n")


def start_codespace_server(
    access: t.Literal["public", "private"] = "private",
    port: int = 8128,
) -> None:
    subprocess.Popen(
        f"python -m http.server {port}",
        shell=True,
    )
    return


NSMAP = {
    "xi": "http://www.w3.org/2001/XInclude",
    "xml": "http://www.w3.org/XML/1998/namespace",
}


def nstag(prefix: str, suffix: str) -> str:
    return "{" + NSMAP[prefix] + "}" + suffix


def copy_custom_xsl(xsl_path: Path, output_dir: Path) -> None:
    xsl_dir = xsl_path.parent.resolve()
    output_dir = output_dir.resolve()
    log.debug(f"Copying all files in {xsl_dir} to {output_dir}")
    shutil.copytree(xsl_dir, output_dir, dirs_exist_ok=True)
    log.debug(f"Copying core XSL to {output_dir}/core")
    shutil.copytree(resources.resource_base_path() / "core" / "xsl", output_dir / "core")
    try:
        symlink = output_dir.parent / "xsl"
        if symlink.exists():
            symlink.unlink()
        symlink.symlink_to(output_dir / "core")
    except Exception as e:
        log.debug(f"Could not create symlink to {output_dir}/core")
        log.debug(e)
        log.debug("Copying core XSL to {symlink} instead.")
        shutil.copytree(resources.resource_base_path() / "core" / "xsl", symlink)


def check_executable(exec_name: str) -> Optional[str]:
    try:
        exec_cmd = core.get_executable_cmd(exec_name)[0]
        log.debug(f"PTX-CLI: Executable command {exec_name} found at {exec_cmd}")
        return exec_cmd
    except OSError as e:
        log.debug(e)
        return None


def check_asset_execs(
    element: str,
    outformats: Optional[List[str]] = None,
    engine: str = "xelatex",
) -> None:
    if outformats is None:
        outformats = []
    log.debug(f"trying to check assets for {element} and output format {outformats}")
    required_execs = []
    if element == "latex-image":
        required_execs = [engine]
        if "eps" in outformats or "all" in outformats:
            required_execs.append("pdfeps")
    if element == "sageplot":
        required_execs = ["sage"]
    install_hints = {
        "xelatex": {
            "Windows": "See https://pretextbook.org/doc/guide/html/windows-cli-software.html",
            "Darwin": "",
            "Linux": "",
        },
        "pdfeps": {
            "Windows": "See https://pretextbook.org/doc/guide/html/windows-cli-software.html",
            "Darwin": "",
            "Linux": "",
        },
        "sage": {
            "Windows": "See https://doc.sagemath.org/html/en/installation/index.html#windows",
            "Darwin": "https://doc.sagemath.org/html/en/installation/index.html#macos",
            "Linux": "See https://doc.sagemath.org/html/en/installation/index.html#linux",
        },
        "pageres": {
            "Windows": "See https://pretextbook.org/doc/guide/html/windows-cli-software.html",
            "Darwin": "",
            "Linux": "",
        },
    }
    for required_exec in required_execs:
        if check_executable(required_exec) is None:
            log.warning(
                f"In order to generate {element} into formats {outformats}, you must have {required_exec} installed, but this appears to be missing or configured incorrectly in pretext.ptx"
            )
            log.info(install_hints.get(required_exec, {}).get(platform.system(), ""))


def clean_asset_table(dirty_table: pt.AssetTable, clean_table: pt.AssetTable) -> pt.AssetTable:
    dirty_table = {asset: dirty_table[asset] for asset in dirty_table if asset in clean_table}
    # for asset in dirty_table:
    #    dirty_table[asset] = {
    #        id: dirty_table[asset][id]
    #        for id in dirty_table[asset]
    #        if id in clean_table[asset]
    #    }
    return dirty_table


def cannot_find_project(task: str) -> bool:
    if project_path() is None:
        log.critical(
            f"Before you can {task} your PreTeXt project, you must be in a (sub)directory initialized with a project.ptx manifest."
        )
        log.critical(
            "Move to such a directory, use `pretext new` to create a new project, or `pretext init` to update existing project for use with the CLI."
        )
        return True
    return False


def show_target_hints(
    target_format: Optional[str],
    project: Any,
    task: str,
) -> None:
    if project.has_target(name=target_format):
        return
    if target_format is None:
        log.critical(
            f"No viable targets found in project.ptx.  The available targets are named: {project.target_names()}."
        )
        return
    log.critical(f'There is not a target named "{target_format}" for this project.ptx manifest.')
    if target_format in constants.FORMATS:
        target_names = project.target_names(target_format)
        if len(target_names) == 1:
            log.info(
                f'However, the target named "{target_names[0]}" has "{target_format}" as its format.  Try to {task} that instead or edit your project.ptx manifest.'
            )
        elif len(target_names) > 1:
            log.info(
                f'However, the targets with names {target_names} have "{target_format}" as their format.  Try to {task} one of those instead or edit your project.ptx manifest.'
            )
        if target_format in ["epub", "kindle"]:
            log.info(
                f"Instructions for setting up a target with the {target_format} format, including the external programs required, can be found in the PreTeXt guide: https://pretextbook.org/doc/guide/html/epub.html"
            )
    else:
        log.info(
            f"The available targets to {task} are named: {project.target_names()}.  Try to {task} on of those instead or edit your project.ptx manifest."
        )


def mjsre_npm_install() -> None:
    with working_directory(resources.resource_base_path() / "core" / "script" / "mjsre"):
        log.info("Attempting to install/update required node packages.")
        try:
            npm_cmd = shutil.which("npm")
            if npm_cmd is None:
                log.warning("Cannot find npm.  Will try to use prebuilt CSS files instead.")
                raise FileNotFoundError
            subprocess.run([npm_cmd, "install", "--engine-strict=true"])
        except Exception as e:
            log.critical("Unable to install required npm packages.  Please see the documentation.")
            log.critical(e)
            log.debug("", exc_info=True)


def ensure_css_node_modules() -> None:
    with working_directory(resources.resource_base_path() / "core" / "script" / "cssbuilder"):
        try:
            node_cmd = shutil.which("node")
            if node_cmd is None:
                log.warning(
                    "Node.js must be installed to build CSS files.  Please install node.js and npm.\n Will try to use prebuilt CSS files instead."
                )
                raise FileNotFoundError
            node_version = subprocess.run([node_cmd, "-v"], capture_output=True)
            log.debug(f"Node version: {node_version.stdout.decode()}")
            if int(node_version.stdout.decode().split(".")[0][1:]) < 18:
                log.warning(
                    "Node version must be at least 18 to build CSS files.  Please update node.js and npm.\n Will try to use prebuilt CSS files instead."
                )
                return
        except Exception as e:
            log.debug(e)
            log.debug("", exc_info=True)
        if Path("node_modules").exists():
            log.debug("Node modules already installed.")
            return
        log.debug("Attempting to install/update required node packages to generate css from sass.")
        try:
            npm_cmd = shutil.which("npm")
            if npm_cmd is None:
                log.warning("Cannot find npm.  Will try to use prebuilt CSS files instead.")
                raise FileNotFoundError
            subprocess.run([npm_cmd, "install", "--engine-strict=true"])
        except Exception as e:
            log.warning(
                "Unable to install npm packages to build css files.  Non-default CSS themes require node.js and npm to be installed.  See https://pretextbook.org/doc/guide/html/node-and-npm.html"
            )
            log.warning(e)
            log.debug("", exc_info=True)


def ensure_dynsub_node_modules() -> None:
    with working_directory(resources.resource_base_path() / "core" / "script" / "dynsub"):
        try:
            node_cmd = shutil.which("node")
            if node_cmd is None:
                log.warning(
                    "Node.js must be installed to extract dynamic substitutions.  Please install node.js and npm."
                )
                raise FileNotFoundError
            node_version = subprocess.run([node_cmd, "-v"], capture_output=True)
            log.debug(f"Node version: {node_version.stdout.decode()}")
            node_version_decode = node_version.stdout.decode().split(".")
            main_version = int(node_version_decode[0][1:])
            sub_version = int(node_version_decode[1])
            if main_version < 22 or (main_version == 22 and sub_version < 10):
                log.error(
                    "Node version must be at least 22.10 to extract dynamic substitutions.  Please update node.js and npm."
                )
                raise FileNotFoundError
        except Exception as e:
            log.debug(e)
            raise e
        if Path("node_modules").exists():
            log.debug("Node modules already installed.")
            return
        log.debug("Attempting to install/update required node packages extract dynamic susbstitutions.")
        try:
            npm_cmd = shutil.which("npm")
            if npm_cmd is None:
                log.warning("Cannot find npm. Install npm and try again.")
                raise FileNotFoundError
            subprocess.run([npm_cmd, "install"])
        except Exception as e:
            log.warning("Unable to install npm packages. Unable to extract dynamic substitutions.")
            log.warning(e)
            raise e


def playwright_install() -> None:
    try:
        log.info("Checking for update for required playwright chromium browser.")
        # subprocess.run("playwright install-deps", shell=True)
        subprocess.run(["playwright", "install", "chromium"])
        log.debug("Installed dependencies to capture interactive previews")
    except Exception as e:
        log.critical("Unable to install required playwright packages.  Please see the documentation.")
        log.critical(e)
        log.debug("", exc_info=True)


def remove_path(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def has_errors(mh: logging.handlers.MemoryHandler) -> bool:
    return len(mh.buffer) > 0


def exit_command(mh: logging.handlers.MemoryHandler) -> None:
    if has_errors(mh):
        log.info("\n----------------------------------------------------")
        log.info("While running pretext, the following errors occurred:\n")
        log.info("(see log messages above or in the 'logs' folder for more information)")
        mh.flush()
        log.info("----------------------------------------------------")
        raise SystemExit(1)
    else:
        log.debug("Completed without errors.")
        log.info("")


def format_docstring_as_help_str(string: str) -> str:
    import re

    lines = (re.sub(r"\s+", " ", line).strip() for line in string.splitlines())
    return " ".join(line if line else "\n\n" for line in lines)


def parse_git_remote(string: str) -> t.List[str]:
    repo_info = list(filter(None, re.split(r"\/|\:|\.git$", string)))
    return repo_info[-2:]


def publish_to_ghpages(
    directory: Path,
    update_source: bool,
    no_push: bool = False,
    cname: t.Optional[str] = None,
) -> None:
    try:
        import git.repo
        import git.exc
        import ghp_import
    except ImportError:
        log.error("Git must be installed to use this feature, but couldn't be found.")
        log.error("Visit https://github.com/git-guides/install-git for assistance.")
        raise ImportError

    try:
        repo = git.repo.Repo(project_path())
    except git.exc.InvalidGitRepositoryError:
        log.info("Initializing project with Git.")
        repo = git.repo.Repo.init(project_path())
        try:
            repo.config_reader().get_value("user", "name")
            repo.config_reader().get_value("user", "email")
        except Exception:
            log.info("Setting up name/email configuration for Git...")
            name = input("Type a name to use with Git: ")
            email = input("Type your GitHub email to use with Git: ")
            with repo.config_writer() as w:
                w.set_value("user", "name", name)
                w.set_value("user", "email", email)
        repo.git.add(all=True)
        repo.git.commit(message="Initial commit")
        repo.active_branch.rename("main")
        log.info("Successfully initialized new Git repository!")
        log.info("")
    log.info(f"Preparing to deploy from active `{repo.active_branch.name}` git branch.\n")
    if repo.bare or repo.is_dirty() or len(repo.untracked_files) > 0:
        log.info("Changes to project source since last commit detected.")
        if update_source:
            log.info("Committing these changes to local Git repository.\n")
            repo.git.add(all=True)
            repo.git.commit(message="Update to PreTeXt project source.")
        else:
            log.warning(
                "Don't forget to either add and commit the changes to your source with git, or run `pretext deploy -u` to have these changes updated automatically."
            )
            log.warning("Just deploying your built project will not save changes to your source on GitHub.`")
    try:
        origin = repo.remotes.origin
    except AttributeError:
        log.warning("Remote GitHub repository is not yet configured.\n")
        log.info("And if you haven't already, create a remote GitHub repository for this project at:")
        log.info("    https://github.com/new")
        log.info('(Do NOT check any "initialize" options.)')
        log.info('On the next page, copy the "HTTPS" version of the URL in the "Quick Setup" section.')
        log.info("")
        repourl = input("Paste url here: ")
        username = repourl.split("/")[-2]
        reponame = repourl.split("/")[-1]
        log.info("")
        log.info("Next, set up a GitHub personal access token. Instructions:")
        log.info(
            "    https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic"
        )
        log.info("Be sure to check the `repo` and `workflow` scopes when generating this token.")
        log.info("")
        pat = input("Paste your personal access token (`ghp_RANDOMCHARCTERS`): ")
        log.info("")
        repourl = f"https://{username}:{pat}@github.com/{username}/{reponame}"
        repo.create_remote("origin", url=repourl)
        origin = repo.remotes.origin
    log.info("Committing your latest build to the `gh-pages` branch.")
    log.info("")
    ghp_import.ghp_import(directory, mesg="Latest build deployed.", nojekyll=True, cname=cname)
    log.info(f"Attempting to connect to remote repository at `{origin.url}`...")
    # log.info("(Your SSH password may be required.)")
    log.info("")
    try:
        repo_user, repo_name = parse_git_remote(origin.url)
        repo_url = f"https://github.com/{repo_user}/{repo_name}/"
        if "github.io" in repo_name:
            pages_url = f"https://{repo_name}"
        else:
            pages_url = f"https://{repo_user}.github.io/{repo_name}/"
    except Exception as e:
        log.error(f"Unable to parse GitHub URL from {origin.url}")
        log.error("Deploy unsuccessful")
        log.debug(e, exc_info=True)
        return
    if no_push:
        log.info("Skipping push to GitHub.  You can push manually with `git push origin gh-pages`.")
        log.info("")
        log.info("Output committed to the `gh-pages` branch.")
        return

    def _report_push_failure(detail: str) -> None:
        log.warning(f"There was an issue connecting to GitHub repository located at {repo_url}\n")
        log.debug(detail)
        log.info("Make sure you have set up authentication for GitHub.  For more information, visit:")
        log.info("    https://docs.github.com/en/authentication")
        log.info(
            "Make sure you can push changes, either from the command line or in VS Code.  Then try to deploy again.\n"
        )
        log.info(
            "You can also try to run `pretext deploy --no-push` to skip this step, then switch to the `gh-pages` branch (using `git checkout gh-pages`) and push manually."
        )
        log.info("")
        log.info(f"(If `{origin.url}` doesn't match your GitHub repository,")
        log.info("use `git remote remove origin` on the command line then try to deploy again.)")
        log.info("")
        log.error("Deploy was unsuccessful.")

    try:
        branch_push_result = origin.push(refspec=f"{repo.active_branch.name}:{repo.active_branch.name}")
        gh_push_result = origin.push(refspec="gh-pages:gh-pages", force=True)
    except git.exc.GitCommandError as e:
        _report_push_failure(str(e))
        return
    error_flags = (
        git.PushInfo.ERROR | git.PushInfo.REJECTED | git.PushInfo.REMOTE_REJECTED | git.PushInfo.REMOTE_FAILURE
    )
    push_errors = [
        info.summary.strip() for info in list(branch_push_result) + list(gh_push_result) if info.flags & error_flags
    ]
    if push_errors:
        _report_push_failure("\n".join(push_errors))
        return
    log.info("")
    log.info("Latest build successfully pushed to GitHub!\n")
    log.info("")
    log.info("To enable GitHub Pages, visit")
    log.info(f"    {repo_url}settings/pages")
    log.info("selecting the `gh-pages` branch with the `/ (root)` folder.\n")
    log.info("Visit")
    log.info(f"    {repo_url}actions/")
    log.info("to check on the status of your GitHub Pages deployment.\n")
    log.info("Your built project will soon be available to the public at:")
    log.info(f"    {pages_url}")


def active_server_port() -> t.Optional[int]:
    for proc in psutil.process_iter():
        if proc is None:
            continue
        if is_pretext_proc(proc):
            log.debug(f"Found pretext server running with pid {proc.pid}")
            if proc.status() not in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                log.debug("Server is stopped.")
                return None
            try:
                port = proc.connections()[0].laddr.port
                log.debug(f"Server is running on port {port}")
                return port
            except Exception as e:
                log.debug(f"Could not get port number. Exception: {e}", exc_info=True)
    log.debug("No pretext server found running.")
    return None


def stop_server(port: t.Optional[int] = None) -> None:
    if port is not None:
        log.debug(f"Terminating server running on port {port}")
        for proc in psutil.process_iter():
            if len(proc.connections()) > 0:
                if (
                    proc.name() == "pretext"
                    and proc.parent().name() == "pretext"
                    and proc.connections()[0].laddr.port == port
                ):
                    log.debug(f"Terminating process with PID {proc.pid} hosting on port {port}")
                    proc.terminate()
    else:
        for proc in psutil.process_iter():
            if is_pretext_proc(proc):
                log.debug(f"Terminating process with PID {proc.pid}")
                proc.terminate()


def pelican_default_settings() -> t.Dict[str, t.Any]:
    config = pelican.settings.DEFAULT_CONFIG
    config["THEME"] = resources.resource_base_path() / "pelican" / "ptx-theme"
    config["RELATIVE_URLS"] = True
    config["TIMEZONE"] = "Etc/UTC"
    config["ARTICLE_PATHS"] = ["updates"]
    config["ARTICLE_URL"] = "updates/{date:%Y%m%d}-{slug}/"
    config["ARTICLE_SAVE_AS"] = config["ARTICLE_URL"] + "index.html"
    config["PAGE_PATHS"] = ["pages"]
    config["PAGE_URL"] = "{slug}/"
    config["PAGE_SAVE_AS"] = config["PAGE_URL"] + "index.html"
    config["FEED_ALL_ATOM"] = None
    config["CATEGORY_FEED_ATOM"] = None
    config["TRANSLATION_FEED_ATOM"] = None
    config["AUTHOR_FEED_ATOM"] = None
    config["AUTHOR_FEED_RSS"] = None
    config["STATIC_PATHS"] = ["images", "static"]
    config["PTX_SHOW_TARGETS"] = "yes"
    return config


def latest_version() -> t.Optional[str]:
    import requests

    url = "https://pypi.org/pypi/pretext/json"
    try:
        response = requests.get(url, timeout=1)
        return response.json()["info"]["version"]
    except Exception as e:
        log.debug("Could not determine latest version of pretext.")
        log.debug(e, exc_info=True)
        return None


def is_earlier_version(v1: str, v2: str) -> bool:
    v1_parts = v1.split(".")
    v2_parts = v2.split(".")
    for i in range(min(len(v1_parts), len(v2_parts))):
        if int(v1_parts[i]) < int(v2_parts[i]):
            return True
        if int(v1_parts[i]) > int(v2_parts[i]):
            return False
    if len(v1_parts) < len(v2_parts):
        return True
    return False


def check_for_updates() -> None:
    last_check = resources.resource_base_path() / "last_update_check.txt"
    current_version = VERSION
    if last_check.exists():
        with open(last_check, "r") as f:
            last_date = f.readline().strip()
            cached_version = f.readline().strip()
        if last_date == str(datetime.date.today()):
            log.debug("Already checked for updates today.")
            if is_earlier_version(current_version, cached_version):
                log.info(
                    f"Version {cached_version.strip()} of pretext is available.  You are currently using version {current_version}."
                )
                log.info("To upgrade, run `pretext upgrade`.")
            return
    latest = latest_version()
    if latest is None:
        log.debug("Could not check for updates.")
        return
    if is_earlier_version(current_version, latest):
        log.info(f"Version {latest} of pretext is available.  You are currently using version {current_version}.\n")
        log.info("To upgrade, run `pretext upgrade`.")
    elif "dev" in current_version:
        log.warning(f"You are using a nightly release, {current_version}.  The latest stable release is {latest}.\n")
    else:
        log.info(f"You are using the latest version of pretext, {current_version}.\n")
    with open(last_check, "w") as f:
        f.write(str(datetime.date.today()) + "\n")
        f.write(latest + "\n")


def report_version() -> None:
    log.info(f"PreTeXt CLI version: {VERSION}")


def is_pretext_proc(proc: psutil.Process) -> bool:
    if proc.name() == "pretext":
        return False
    parent = proc.parent()
    return parent is not None and parent.name() == "pretext"


def is_unmodified(
    resource: str,
    contents: bytes,
    resource_hash_table: Any = resources.get_resource_hash_table(),
) -> bool:
    lines = contents.decode().splitlines()
    if "<!-- Managed automatically by PreTeXt authoring tools -->" in contents.decode():
        log.debug(f"Resource file {resource} is managed by PreTeXt using magic comment.")
        return True
    for i in range(min(2, len(lines))):
        if "automatically generated with PreTeXt" in lines[i]:
            version = re.search(r"\d+\.\d+\.\d+", lines[i])
            if resource == "requirements.txt" and version:
                return True
            elif version and version[0] in resource_hash_table:
                hash = hashlib.sha256()
                hash.update(contents)
                if hash.hexdigest() == resource_hash_table[version[0]].get(resource):
                    log.debug(f"Resource file {resource} is unmodified, compared to hash.")
                    return True
            break
    log.debug(f"Resource file {resource} appears to have been modified.")
    return False


def rs_methods(url: str = "", out_path: str = "", format: str = "xml") -> t.Optional[str]:
    cache_dir = resources.resource_base_path() / "rs_cache"
    if not cache_dir.exists():
        cache_dir.mkdir()
    if format == "xml":
        assert url != "", "URL must be provided to download xml file."
        assert out_path == "", "Output path must not be provided to download xml file."
        try:
            log.info(f"Downloading rs services file from {url}.")
            services_xml = core.query_runestone_services(url)
            with open(cache_dir / "rs_services.xml", "w") as f:
                f.write(services_xml)
        except Exception as e:
            log.warning(f"Could not download rs services file from {url}.  Using cached version instead.")
            log.debug(e)
            with open(cache_dir / "rs_services.xml", "r") as f:
                services_xml = f.read()
        finally:
            return services_xml

    elif format == "tgz":
        assert url != "", "URL must be provided to download tgz file."
        assert out_path != "", "Output path must be provided to download tgz file."

        services_filename = url.split("/")[-1]
        services_cache_path = cache_dir / services_filename
        if not services_cache_path.exists():
            try:
                log.debug(f"Downloading rs services file from {url} to {services_cache_path}.")
                core.download_file(url, services_cache_path)
            except Exception as e:
                log.warning(f"Could not download rs services file from {url} and no cached version found.")
                raise e
        out_dir = Path(out_path).parent
        if not out_dir.exists():
            out_dir.mkdir(parents=True)
        log.debug(f"Extracting rs services file to {out_dir}.")
        shutil.copyfile(services_cache_path, out_path)

    else:
        log.error(
            f"PTX-BUG: Format {format} not recognized for running ext_rs_methods.  Something is wrong with the pretext script."
        )
    return None


class Stopwatch:
    """print_log set to false disables logging of elapsed time"""

    def __init__(self, name: str = "", print_log: bool = True):
        self.name = name
        self.print_log = print_log
        self.start_time = time.time()
        self.last_log_time = self.start_time

    def reset(self) -> None:
        self.last_log_time = time.time()

    def log(self, timepoint_description: str = "") -> None:
        if self.print_log:
            cur_time = time.time()
            elapsed_time = cur_time - self.start_time
            since_last_log_time = cur_time - self.last_log_time
            self.reset()
            log.debug(
                f"** Timing report from {self.name}: {timepoint_description}, {since_last_log_time:.2f}s since last watch reset. {elapsed_time:.2f}s total elapsed time."
            )
