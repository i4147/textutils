import importlib
import importlib.util
import sys
import click
import click_log
import shutil
import os
import zipfile
import requests
import io
import tempfile
import platform
import webbrowser
from pathlib import Path
import subprocess
from pydantic import ValidationError
from typing import Any, Callable, List, Literal, Optional
from functools import update_wrapper

from . import (
    utils,
    resources,
    constants,
    logger,
    server,
    VERSION,
    CORE_COMMIT,
)

from .project import Project

log = logger.log
logger.add_log_stream_handler()
error_flush_handler = logger.get_log_error_flush_handler()


def nice_errors(f: Callable[..., None]) -> Any:
    @click.pass_context
    def try_except(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        try:
            return ctx.invoke(f, *args, **kwargs)
        except ValidationError as e:
            log.critical(
                "Failed to parse project.ptx. Check the entire file, including all targets, and fix the following errors:"
            )
            for error in e.errors():
                if error["type"] == "missing":
                    log.error(
                        f"One of the targets has a missing required attribute: {error['loc'][0]}; look for the target with {error['input']}."
                    )
                elif error["type"] == "enum":
                    log.error(
                        f'One of the targets has an attribute with illegal value: @{error["loc"][0]}="{error["input"]}" is not allowed.  Pick from the values:{error["msg"].split(": ")[-1].replace("Input should be", "")}.'
                    )
                elif error["type"] == "extra_forbidden":
                    log.error(
                        f'Either one of the targets or the root project element has an extra attribute it shouldn\'t: {error["loc"][0]}="{error["input"]}"'
                    )
                elif error["type"] == "value_error":
                    log.error(
                        f'In at least one target, you cannot have @{error["loc"][0]}="{error["input"]}".  {error["msg"].replace("Value error, ", "")}'
                    )
                else:
                    log.error(f"{error['msg']} ({error['loc']}; {error['type']})")
            log.debug(
                "\n------------------------\nException info:\n------------------------\n",
                exc_info=True,
            )
            return
        except Exception as e:
            log.error(e)
            log.debug("Exception info:\n------------------------\n", exc_info=True)
            return

    return update_wrapper(try_except, f)


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

_VERBOSITY_HELP = "Sets the severity of log messaging: DEBUG for all, INFO (default) for most, then WARNING, ERROR, and CRITICAL for decreasing verbosity."


def set_log_level(_ctx: click.Context, _param: click.Parameter, value: Optional[str]) -> None:
    _ = (_ctx, _param)
    if value:
        log.setLevel(value.upper())


class PreTeXtGroup(click.Group):
    def command(self, *args: Any, **kwargs: Any) -> Any:
        original_decorator = super().command(*args, **kwargs)

        def decorator(f: Callable[..., Any]) -> Any:
            f = click.option(
                "--verbosity",
                "-v",
                default=None,
                expose_value=False,
                is_eager=True,
                callback=set_log_level,
                type=click.Choice(
                    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    case_sensitive=False,
                ),
                help=_VERBOSITY_HELP,
            )(f)
            return original_decorator(f)

        return decorator


@click.group(cls=PreTeXtGroup, invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click_log.simple_verbosity_option(
    log,
    help="Sets the severity of log messaging: DEBUG for all, INFO (default) for most, then WARNING, ERROR, and CRITICAL for decreasing verbosity.",
)
@click.version_option(VERSION, message=VERSION)
@click.option(
    "-t",
    "--targets",
    is_flag=True,
    help='Display list of build/view "targets" available in the project manifest.',
)
@click.option(
    "--save-tmp-dirs",
    is_flag=True,
    help="Do not clean temporary directories after a build or generate.  Might be useful for debugging (previously calling -v debug would also save these directories).",
)
@nice_errors
def main(ctx: click.Context, targets: bool, save_tmp_dirs: bool) -> None:

    if targets:
        if (pp := utils.project_path()) is not None:
            project = Project.parse(pp)
            for target in project.target_names():
                print(target)
        else:
            log.warning("Not inside a project, cannot list targets")
        return

    utils.check_for_updates()

    if ctx.invoked_subcommand is None:
        log.info("Run `pretext --help` for help.")
        return

    if ctx.invoked_subcommand == "upgrade":
        log.debug("Upgrading project now")
        return
    if ctx.invoked_subcommand == "update":
        log.debug("Updating project now")
        return

    if (pp := utils.project_path()) is not None:
        project = Project.parse(pp)
        log.info(f"PreTeXt project found in `{utils.project_path()}`.")

        logger.add_log_file_handler(pp / "logs")

        os.chdir(pp)
        if utils.requirements_version() is None:
            log.warning("Project's CLI version could not be detected from `requirements.txt`.")
            log.warning("Try `pretext update-project` to produce a compatible file.")
        elif utils.requirements_version() != VERSION:
            log.warning(f"Using CLI version {VERSION} but project's `requirements.txt`")
            log.warning(f"is configured to use {utils.requirements_version()}. Consider either installing")
            log.warning(f"CLI version {utils.requirements_version()} or running `pretext update-project`")
            log.warning(f"to update `requirements.txt` and other managed files to match {VERSION}.")
        else:
            log.debug(f"CLI version {VERSION} matches requirements.txt {utils.requirements_version()}.")

    else:
        if ctx.invoked_subcommand == "new":
            return

        log.info(f"PreTeXt-CLI version: {VERSION}\n")
        utils.ensure_default_project_manifest()
        default_project_path = resources.resource_base_path() / "project.ptx"
        project = Project.parse(default_project_path, global_manifest=True)
        log.warning(
            f"No project.ptx manifest found in current workspace.  Using global configuration specified in '~/.ptx/{VERSION}/project.ptx'."
        )

    ctx.obj = {"project": project, "save_tmp_dirs": save_tmp_dirs}


@main.result_callback()
def exit(*_, **__):

    utils.exit_command(error_flush_handler)


@main.command(
    short_help="Upgrade PreTeXt-CLI to the latest version using pip.",
    context_settings=CONTEXT_SETTINGS,
)
def upgrade() -> None:
    extras = []
    if importlib.util.find_spec("prefig") is not None:
        log.debug("The 'prefig' package is installed; will attempt to upgrade it as well.")
        extras.append("prefigure")
    if importlib.util.find_spec("pelican") is not None:
        log.debug("The 'pelican' package is installed; will attempt to upgrade it as well.")
        extras.append("homepage")
    if len(extras) > 0:
        log.info(f"Upgrading PreTeXt (with extras: {', '.join(extras)})")
        pretext_cmd = "pretext[" + ",".join(extras) + "]"
    else:
        log.info("Upgrading PreTeXt.")
        pretext_cmd = "pretext"
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pretext_cmd])
    log.info(
        "Upgrade complete.  Individual projects can be updated to align with the latest version of the CLI by running `pretext update-project` from their project folder."
    )


@click.command("update")
def old_update() -> None:
    click.echo("This command is outdated. Use `pretext update-project` instead.")


@main.command(
    "update-project",
    short_help="Update the current project to match the installed version of PreTeXt.  Note: to upgrade the installed version of pretext, use `pretext upgrade`.",
    context_settings=CONTEXT_SETTINGS,
)
@click.option("-b", "--backup", is_flag=True, help="Backup project files before updating.")
@click.option("-f", "--force", is_flag=True, help="Force update of project files.")
def update_project(backup: bool, force: bool) -> None:
    if utils.cannot_find_project(task="update"):
        log.info(
            "Did you mean to run `pretext upgrade` to upgrade to the latest installed version of PreTeXt, or are you trying to update a particular project?"
        )
        return
    project = Project.parse()
    project.update_boilerplate(backup=backup, force=force)
    log.info("Project updated successfully.")


@main.command(
    short_help="Use when communicating with PreTeXt support.",
    context_settings=CONTEXT_SETTINGS,
)
@nice_errors
def support() -> None:
    log.debug("Running pretext support.")
    log.info("")
    log.info("Please share the following information when posting to the")
    log.info("pretext-support Google Group.")
    log.info("")
    log.info(f"PreTeXt-CLI version: {VERSION}")
    log.info(f"    PyPI link: https://pypi.org/project/pretextbook/{VERSION}/")
    log.info(f"PreTeXt core resources commit: {CORE_COMMIT}")

    log.info(f"OS: {platform.platform()}")
    log.info(f"Python version: {platform.python_version()}, running from {sys.executable}")
    log.info(f"Current working directory: {Path.cwd()}")
    if utils.project_path() is not None:
        log.info(f"PreTeXt project path: {utils.project_path()}")
        log.info("")
        log.info("Contents of project.ptx:")
        log.info("------------------------")
        log.info(utils.project_xml_string())
        log.info("------------------------")

        project = Project.parse()
        project.init_core()

        for exec_name in project.get_executables().model_dump():
            if utils.check_executable(exec_name) is None:
                log.warning(f"Unable to locate the command for `{exec_name}` on your system.")
    else:
        log.info("No project.ptx found.")


@main.command(
    short_help="Alias for the developer pretext/pretext script.",
    context_settings={"help_option_names": [], "ignore_unknown_options": True},
)
@click.argument("args", nargs=-1)
def devscript(args: List[str]) -> None:
    subprocess.run(
        [
            sys.executable,
            str(resources.resource_base_path() / "core" / "pretext" / "pretext"),
        ]
        + list(args)
    )


@main.command(
    short_help="Generates all the necessary files for a new PreTeXt project.",
    context_settings=CONTEXT_SETTINGS,
)
@click.argument(
    "template",
    default="book",
    type=click.Choice(constants.NEW_TEMPLATES, case_sensitive=False),
)
@click.option(
    "-d",
    "--directory",
    type=click.Path(),
    default="new-pretext-project",
    help="Directory to create/use for the project.",
)
@click.option(
    "-u",
    "--url-template",
    type=click.STRING,
    help="Download a zipped template from its URL.",
)
@nice_errors
def new(template: str, directory: Path, url_template: str) -> None:
    directory_fullpath = Path(directory).resolve()
    if utils.project_path(directory_fullpath) is not None:
        log.error(
            f"A project already exists in `{utils.project_path(directory_fullpath)}` (it contains the file `project.ptx`)."
        )
        log.error("No new project will be generated.")
        return
    log.info(f"Generating new PreTeXt project in `{directory_fullpath}`")
    directory_fullpath.mkdir(exist_ok=True)
    if url_template is not None:
        log.info(f"Using template at `{url_template}`")

        r = requests.get(url_template)
        archive = zipfile.ZipFile(io.BytesIO(r.content))
        with tempfile.TemporaryDirectory(prefix="ptxcli_") as tmpdirname:
            archive.extractall(tmpdirname)
            content_path = [Path(tmpdirname) / i for i in os.listdir(tmpdirname)][0]
            shutil.copytree(content_path, directory_fullpath, dirs_exist_ok=True)
    else:
        log.info(f"Using `{template}` template.")

        template_path = resources.resource_base_path() / "templates" / f"{template}"
        shutil.copytree(template_path, directory_fullpath, dirs_exist_ok=True)

        with utils.working_directory(directory_fullpath):
            project_path = utils.project_path()
            if project_path is None:
                project = Project()
            else:
                project = Project.parse(project_path)

            project.update_boilerplate()


@main.command(
    short_help="Generates/updates CLI-specific files for the current version of PreTeXt-CLI.",
    context_settings=CONTEXT_SETTINGS,
)
@click.option(
    "-r",
    "--refresh",
    is_flag=True,
    help="Refresh initialization of project even if project.ptx exists. [This will be deprecated in the future; use `pretext update -f` instead.] ",
)
@click.option(
    "-f",
    "--file",
    "files",
    help="Specify file to refresh.",
    multiple=True,
    type=click.Choice([r for r in constants.PROJECT_RESOURCES], case_sensitive=False),
)
@click.option(
    "-s",
    "--system",
    is_flag=True,
    help="Reinstall's the system's pretext resources, including the core pretext script, templates, and other resources (including npm installs).  Useful if something is broken or after initial installation or upgrade.",
)
@nice_errors
def init(refresh: bool, files: List[str], system: bool) -> None:
    if system:
        log.info("Reinstalling system resources...")
        resources.install(reinstall=True, npm_install=True)
        log.info("System resources reinstalled successfully.")
        return
    project_path = utils.project_path()
    if project_path is None:
        project = Project()
    else:
        if refresh or len(files) > 0:
            project = Project.parse(project_path)
            if refresh:
                log.warning(
                    "The `pretext init --refresh` command will be deprecated in a future version.  You can use `pretext update --force` instead."
                )
        else:
            log.warning(f"A project already exists in `{project_path}`.")
            log.warning("Use `pretext update --force` to refresh initialization of an existing project")
            log.warning("or `pretext init --file FILENAME` to refresh a specific file.")
            return

    if len(files) > 0:
        for file in files:
            if file.lower() in constants.PROJECT_RESOURCES:
                project.add_boilerplate(file.lower(), backup=True)
            else:
                log.error(f"File {file} is not a valid project resource.")
        return
    project.update_boilerplate(backup=True, force=True)

    if project_path is None:
        log.info("Success! Open project.ptx to edit your project manifest.")
        log.info("Edit your `target` elements to point to the location of your PreTeXt source files.")
    else:
        log.info("Success! Your project files have been refreshed. If you manage any of these")
        log.info("manually, be sure to compare these new versions with your old .bak files.")


@main.command(short_help="Build specified target", context_settings=CONTEXT_SETTINGS)
@click.argument("target_name", required=False, metavar="target")
@click.option(
    "--clean",
    is_flag=True,
    help="Destroy output's target directory before build to clean up previously built files",
)
@click.option(
    "-g",
    "--generate",
    is_flag=True,
    help="Force (re)generates assets for targets, even if they haven't changed since they were last generated.  (Use `pretext generate` for more fine-grained control of manual asset generation.)",
)
@click.option(
    "-q",
    "--no-generate",
    is_flag=True,
    help="Do not generate assets for target, even if their source has changed since the last time they were generated.",
)
@click.option(
    "-t",
    "--theme",
    is_flag=True,
    help="Only build the theme for the target, without performing any other build or generate steps.  (Themes are automatically built when building a target.)",
)
@click.option(
    "-l",
    "--latex",
    is_flag=True,
    help="When building a PDF, also place LaTeX source files in the output directory for inspection or manual compilation.",
)
@click.option(
    "-x",
    "--xmlid",
    type=click.STRING,
    help="xml:id of the root of the subtree to be built.",
)
@click.option(
    "--no-knowls",
    is_flag=True,
    help="Use hyperlinks instead of knowls (e.g. for previewing individual sections when knowl files from other sections may not exist)",
)
@click.option(
    "--deploys",
    is_flag=True,
    help="Build all targets configured to be deployed.",
)
@click.option(
    "-i",
    "--input",
    "source_file",
    type=click.Path(),
    help="Override the source file from the manifest by providing a path to the input.",
)
@click.pass_context
@nice_errors
def build(
    ctx: click.Context,
    target_name: Optional[str],
    clean: bool,
    generate: bool,
    no_generate: bool,
    theme: bool,
    latex: bool,
    xmlid: Optional[str],
    no_knowls: bool,
    deploys: bool,
    source_file: Optional[str],
) -> None:

    project = ctx.obj["project"]
    save_tmp_dirs = ctx.obj.get("save_tmp_dirs", False)

    if target_name and Path(target_name).is_file():
        log.debug(f"target is a source file {Path(target_name).resolve()}.  Using this to override input.")
        log.warning("Building standalone documents is an experimental feature and the interface may change.")

        source_file = target_name
        target_name = None

    try:
        if deploys and len(project.deploy_targets()) > 0:
            targets = project.deploy_targets()
        elif target_name is None and source_file is not None:
            if len(project.standalone_targets()) > 0:
                targets = [project.standalone_targets()[0]]
                log.debug(f"Building standalone document with target {targets[0].name}")
            else:
                log.debug("Did not find a standalone project manifest.")
                target = project.new_target(
                    name="standalone",
                    format="pdf",
                    standalone="yes",
                    output_dir=Path(source_file).resolve().parent,
                )
                targets = [target]
                log.debug(f"Building standalone document with target {target.name}")
        else:
            targets = [project.get_target(name=target_name)]
    except AssertionError as e:
        log.warning("Assertion error in getting target.")
        utils.show_target_hints(target_name, project, task="build")
        log.exit("Exiting without completing build.")
        log.debug(e, exc_info=True)
        return

    if theme:
        try:
            for t in targets:
                t.ensure_webwork_reps()
                t.ensure_myopenmath_xml()
                t.build_theme()
        except Exception as e:
            log.error(f"Failed to build theme: {e}")
            log.debug("Exception info:\n------------------------\n", exc_info=True)
        finally:
            return

    if source_file is not None:
        for t in targets:
            t.source = Path(source_file).resolve()
            log.warning(f"Overriding source file for target with: {t.source}")

    if generate and not no_generate:
        try:
            for t in targets:
                log.info(f"Generating assets for {t.name}")
                t.generate_assets(
                    only_changed=False,
                    xmlid=xmlid,
                    clean=clean,
                    skip_cache=True,
                    clean_tmp_dirs=not save_tmp_dirs,
                )
            no_generate = True
        except Exception as e:
            log.error(f"Failed to generate assets: {e} \n")
            log.debug("Debug Info:\n", exc_info=True)
    elif generate and no_generate:
        log.warning(
            "Using the `-g/--generate` flag together with `-q/--no-generate` doesn't make sense.  Proceeding as if neither flag was set."
        )
        generate = False
        no_generate = False

    try:
        for t in targets:
            log.info(f"Building target {t.name}")
            if xmlid is not None:
                log.info(f"with root of tree below {xmlid}")
            t.build(
                clean=clean,
                generate=not no_generate,
                xmlid=xmlid,
                no_knowls=no_knowls,
                latex=latex,
                clean_tmp_dirs=not save_tmp_dirs,
            )
            if t.format == "html" and t.compression is None:
                log.info(f"\nFinished build for target {t.name}. Run `pretext view {t.name}` to see the results.\n")
            else:
                log.info(f"\nFinished build for target {t.name}. The output is in {t.output_dir_abspath()}.\n")

        if utils.has_errors(error_flush_handler):
            raise Exception("There were errors during the build.  See above.")

        log.info("\nSuccess!  Built requested target(s) without errors.\n")
    except ValidationError as e:
        log.critical("It appears there is an error with your project.ptx or publication file.  See the details below.")
        log.critical(e)
        log.exit("Failed to build without errors.  Exiting...")
        log.debug(
            "\n------------------------\nException info:\n------------------------\n",
            exc_info=True,
        )
        return
    except Exception as e:
        log.critical(e)
        log.debug("Exception info:\n------------------------\n", exc_info=True)
        log.info("------------------------")
        log.exit("Failed to build without errors.  Exiting...")
        return


@main.command(
    short_help="Validate source against the PreTeXt schema",
    context_settings=CONTEXT_SETTINGS,
)
@click.argument("target_name", required=False, metavar="target")
@click.option(
    "--method",
    type=click.Choice(["local", "server"]),
    default="local",
    show_default=True,
    help='Where the schema checks run: "local" (an installed jing) or "server" '
    "(jing as a remote service, needing no local install).",
)
@click.option(
    "--report-form",
    type=click.Choice(["full", "terse"]),
    default="full",
    show_default=True,
    help='The shape of the report: "full" (locations, excerpts, and '
    'explanations, meant to be read) or "terse" (machine-readable, one '
    "tab-separated message per line).",
)
@click.option(
    "--engine",
    type=click.Choice(["jing", "salve"]),
    default="jing",
    show_default=True,
    help='Which RelaxNG engine performs the check. EXPERIMENTAL: "salve" uses '
    "the validator behind the pretext-tools VS Code extension instead of jing, "
    "and needs no Java (it installs itself with npm on first use). It finds the "
    "same problems but words them differently, so reports are not comparable "
    "line for line. Ignored by `--method server`.",
)
@click.pass_context
@nice_errors
def validate(
    ctx: click.Context,
    target_name: Optional[str],
    method: str,
    report_form: str,
    engine: str,
) -> None:
    project = ctx.obj["project"]
    target = project.get_target(target_name)

    try:
        target.source_element()
    except Exception as e:
        log.error(f"Could not assemble source for validation: {e}")
        raise SystemExit(1)

    log.info(
        f"Validating source of target {target.name} (method: {method}, report form: {report_form}, engine: {engine})."
    )
    if engine == "salve":
        log.warning(
            "The salve engine is experimental. Its messages are worded "
            "differently from jing's, so a report from it will not match a "
            "report from jing line for line."
        )
    result = target.validate_source(method=method, engine=engine, report_form=report_form)

    if result is None:
        log.error("Validation could not be performed.")
        log.error(
            "Install jing and make sure it is on your PATH (or name it in "
            "executables.ptx), or use `pretext validate --method server` or "
            "`pretext validate --engine salve`."
        )
        raise SystemExit(2)

    message_count, experimental_count, report = result
    if experimental_count:
        log.info(
            f"Experimental constructs are in use at {experimental_count} "
            "locations; the report surveys them. They are not errors, but "
            "their markup may change without a deprecation cycle."
        )
    if message_count == 0:
        log.info("PreTeXt source passed validation with no messages.")
        log.info(f"Report: {report}")
        return
    log.error(f"PreTeXt source did NOT pass validation ({message_count} messages).")
    log.error(f"See {report} for the full report.")
    raise SystemExit(1)


@main.command(
    short_help="Generate specified assets for default target or targets specified by `-t`",
    context_settings=CONTEXT_SETTINGS,
)
@click.argument("assets", type=click.Choice(constants.ASSETS, case_sensitive=False), nargs=-1)
@click.option(
    "-t",
    "--target",
    "target_name",
    type=click.STRING,
    help="Name of target to generate assets for (if not specified, first target from manifest is used).",
)
@click.option("-x", "--xmlid", type=click.STRING, help="xml:id of element to be generated.")
@click.option(
    "-q",
    "--only-changed",
    is_flag=True,
    default=False,
    help="Limit generation of assets to only those that have changed since last call to pretext.",
)
@click.option(
    "--all-formats",
    is_flag=True,
    default=False,
    help="Generate all possible asset formats rather than just the defaults for the specified target.",
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help="Remove all generated assets, including the cache, before generating new ones.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force generation of assets; do not rely on assets in the cache.",
)
@click.option(
    "-s",
    "--slow",
    is_flag=True,
    default=False,
    help="Increase the timeout for capturing screenshots of interactive elements.  Only needed if some interactive previews are not rendering correctly.",
)
@click.pass_context
@nice_errors
def generate(
    ctx: click.Context,
    assets: List[str],
    target_name: Optional[str],
    all_formats: bool,
    only_changed: bool,
    xmlid: Optional[str],
    clean: bool,
    force: bool,
    slow: bool,
) -> None:

    if assets == ():
        assets = ["ALL"]

    if utils.cannot_find_project(task="generate assets for"):
        return

    project = ctx.obj["project"]
    save_tmp_dirs = ctx.obj.get("save_tmp_dirs", False)

    try:
        target = project.get_target(name=target_name)
    except AssertionError as e:
        utils.show_target_hints(target_name, project, task="generating assets for")
        log.exit("Exiting without completing build.")
        log.debug(e, exc_info=True)
        return

    try:
        log.debug(f'Generating assets in for the target "{target.name}".')
        target.generate_assets(
            requested_asset_types=assets,
            all_formats=all_formats,
            only_changed=only_changed,
            xmlid=xmlid,
            clean=clean,
            skip_cache=force,
            slow=slow,
            clean_tmp_dirs=not save_tmp_dirs,
        )

        if utils.has_errors(error_flush_handler):
            raise Exception("There were errors during the generate process.  See above.")

        log.info("Finished generating assets successfully.\n")
    except ValidationError as e:
        log.critical("It appears there is an error with your project.ptx or publication file.  See the details below.")
        log.critical(e)
        log.exit("Failed to build.  Exiting...")
        log.debug(
            "\n------------------------\nException info:\n------------------------\n",
            exc_info=True,
        )
        return
    except Exception as e:
        log.critical(e)
        log.debug("Exception info:\n------------------------\n", exc_info=True)
        log.info("------------------------")
        log.exit("Generating assets as failed.  Exiting...")
        return


@main.command(
    short_help="Preview specified target based on its format.",
    context_settings=CONTEXT_SETTINGS,
)
@click.argument("target_name", metavar="target", required=False)
@click.option(
    "-a",
    "--access",
    type=click.Choice(["public", "private"], case_sensitive=False),
    default="private",
    show_default=True,
    help="""
    If running a local server,
    choose whether or not to allow other computers on your local network
    to access your documents using your IP address.
    """,
)
@click.option(
    "-p",
    "--port",
    type=click.INT,
    default=8128,
    help="""
    If running a local server,
    choose which port to use.
    (Ignored when used
    in CoCalc, which works automatically.)
    """,
)
@click.option(
    "-b",
    "--build",
    is_flag=True,
    help="""
    Run a build before viewing.
    """,
)
@click.option(
    "-g",
    "--generate",
    is_flag=True,
    help="Generate all assets before viewing",
)
@click.option(
    "--no-launch",
    is_flag=True,
    help="By default, pretext view tries to launch the default application to view the specified target.  Setting this suppresses this behavior.",
)
@click.option(
    "-r",
    "--restart-server",
    is_flag=True,
    default=False,
    help="Force restart the local http server in case it is already running.",
)
@click.option(
    "-s",
    "--stop-server",
    is_flag=True,
    default=False,
    help="Stop the local http server if running.",
)
@click.option(
    "-d",
    "--stage",
    is_flag=True,
    default=False,
    help="View the staged deployment.",
)
@click.option(
    "--default-server",
    is_flag=True,
    default=False,
    help="Use the standard python server, even if in a codespace (for debugging)",
)
@click.pass_context
@nice_errors
def view(
    ctx: click.Context,
    target_name: str,
    access: Literal["public", "private"],
    port: int,
    build: bool,
    generate: bool,
    no_launch: bool,
    restart_server: bool,
    stop_server: bool,
    stage: bool,
    default_server: str,
) -> None:

    if utils.cannot_find_project(task="view the output for"):
        return
    project = Project.parse()
    project_hash = utils.hash_path(project.abspath())
    current_server = server.active_server_for_path_hash(project_hash)
    if stop_server:
        try:
            log.info("\nStopping server.")
            if current_server:
                current_server.terminate()
        except Exception as e:
            log.warning("Failed to stop server.")
            log.debug(e, exc_info=True)
        finally:
            return

    try:
        target = project.get_target(name=target_name, log_info_for_none=not stage)
    except AssertionError as e:
        utils.show_target_hints(target_name, project, task="view")
        log.exit("Exiting.")
        log.debug(e, exc_info=True)
        return

    if generate:
        try:
            target.generate_assets(only_changed=False)
        except Exception as e:
            log.warning(f"Failed to generate assets: {e}")
            log.debug("", exc_info=True)

    if build:
        try:
            target.build()
        except Exception as e:
            log.warning(f"Failed to build: {e}")
            log.debug("Exception info:\n------------------------\n", exc_info=True)

    if stage:
        target_name = "staged deployment"
        url_path = "/" + project.stage.as_posix()
    else:
        target_name = f"target `{target.name}`"
        url_path = "/" + target.output_dir_relpath().as_posix()

    in_codespace = os.environ.get("CODESPACES")

    if restart_server and current_server is not None:
        log.info(f"Terminating existing server {current_server.pid} on port {current_server.port}")
        current_server.terminate()
        current_server = None

    if current_server is not None and current_server.is_active_server():
        url_base = utils.url_for_access(access=access, port=current_server.port)
        url = url_base + url_path
        log.info(f"Server is already available at {url_base}")
        if no_launch:
            log.info(f"The {target_name} is available at {url}")
        else:
            log.info(f"Now opening browser for {target_name} at {url}")
            webbrowser.open(url)

    else:
        log.info(f"Now preparing local server to preview your project directory `{project.abspath()}`.")
        log.info("  (Reminder: use `pretext deploy` to deploy your built project to a public")
        log.info("  GitHub Pages site that can be shared with readers who cannot access your")
        log.info("  personal computer.)")
        log.info("")

        def callback(actual_port: int) -> None:
            url_base = utils.url_for_access(access=access, port=actual_port)
            url = url_base + url_path
            log.info(f"Server will soon be available at {url_base}")
            if no_launch:
                log.info(f"The {target_name} will be available at {url}")
            else:
                log.info(f"Opening browser for {target_name} at {url}")
                webbrowser.open(url)

        log.info("starting server ...")
        if in_codespace and not default_server:
            log.info("Running in a codespace, so using a subprocess server.")
            server.start_codespace_server(project.abspath(), access, port, callback)
        else:
            server.start_server(project.abspath(), access, port, callback)


@main.command(
    short_help="Deploys Git-managed project to GitHub Pages.",
    context_settings=CONTEXT_SETTINGS,
)
@nice_errors
@click.pass_context
@click.option(
    "-u",
    "--update-source",
    is_flag=True,
    required=False,
    help="Commit and push changes tot he source files at the same time as deploying output.",
)
@click.option(
    "-s",
    "--stage-only",
    is_flag=True,
    required=False,
    help="Create a staged deployment, but do not deploy.",
)
@click.option(
    "-p",
    "--preview",
    is_flag=True,
    required=False,
    help="Preview the staged deployment, but do not actually deploy.",
)
@click.option(
    "--no-push",
    is_flag=True,
    required=False,
    help="Commit output to gh-pages branch but do not push to GitHub.  Useful in case of authentication errors.",
)
def deploy(
    ctx: click.Context,
    update_source: bool,
    stage_only: bool,
    preview: bool,
    no_push: bool,
) -> None:
    if utils.cannot_find_project(task="deploy"):
        return
    project = ctx.obj["project"]
    project.stage_deployment()
    if stage_only:
        return
    if preview:
        ctx.invoke(view, stage=True)
    else:
        project.deploy(update_source=update_source, skip_staging=True, no_push=no_push)
