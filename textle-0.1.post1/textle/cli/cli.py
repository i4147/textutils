import os
import sys
import time
import click
from colorama import Back, Fore
from watchdog.observers import Observer
from .autre import interpret_extra_options
from ..parsers import textlefile
from ..textlefile import SEV_DBG, SEV_ERROR, SEV_INFO, Textle

root_dir = None
textlefile_name = None
textlefile_path = None
verbose_level = 2


def build_message_handler(task, sev, msg):
    if sev > verbose_level:
        return
    sev, color = {SEV_ERROR: ("error", "red"), SEV_DBG: ("debug", "cyan"), SEV_INFO: ("info", "white")}[sev]
    click.secho("[{}] [{}] {}".format(sev, task, msg), fg=color)


@click.group()
@click.option(
    "-C",
    "--project",
    "root_di",
    default=os.getcwd,
    type=click.Path(writable=True, resolve_path=True, file_okay=False),
    help="Operate on a different directory",
)
@click.option("-T", "--textlefile", default="Textlefile", type=str)
@click.option("-q", "--quiet", count=True, help="Make less output; sums with verbose")
@click.option("-v", "--verbose", count=True, help="Make more output; sums with quiet")
@click.version_option()
def textle(root_di, quiet, verbose, textlefile):
    global root_dir, verbose_level, textlefile_name, textlefile_path
    root_dir = root_di
    textlefile_name = textlefile
    textlefile_path = os.path.join(root_dir, textlefile_name)
    verbose_level += verbose - quiet


@textle.command(context_settings=dict(ignore_unknown_options=True))
@click.option("--overwrite", is_flag=True, default=False, help="Always overwrite an existing Textlefile")
@click.argument("pipelines_and_options", type=str, nargs=-1)
def new(pipelines_and_options, overwrite):
    count = 0
    for i in pipelines_and_options:
        if i[0] != "-":
            count += 1
        else:
            break
    pipelines = pipelines_and_options[:count]
    options = pipelines_and_options[count:]
    glob_opts, intern_opts = interpret_extra_options(options)
    textlefile_source = textlefile.create_textlefile_string_from(pipelines, glob_opts, intern_opts)
    if os.path.exists(textlefile_path) and not (
        overwrite or click.confirm("Are you sure you want to overwrite the existing configuration?")
    ):
        sys.exit(1)
    with open(textlefile_path, "w") as f:
        f.write(textlefile_source)
    if verbose_level >= 1:
        click.secho("Created textlefile!", fg="cyan")
        if verbose_level >= 2:
            click.secho("To get started, try the following:", fg="cyan")
            click.echo(Fore.CYAN + "\t- " + Fore.WHITE + "textle go " + Fore.CYAN + "to build.")
            click.echo(
                Fore.CYAN + "\t- " + Fore.WHITE + "textle live " + Fore.CYAN + "to build and view the output live."
            )


@textle.command()
@click.option(
    "--from", "source_file", default=None, type=str, help="Build the file that uses this input, instead of all of them."
)
def go(source_file):
    if not os.path.exists(textlefile_path):
        click.echo("There isn't a project here!", err=True)
        sys.exit(1)
    try:
        with open(textlefile_path, "r") as f_:
            f = textlefile.textlefile_from_string(f_.read(), root_dir).with_job_callback(build_message_handler)
    except IOError:
        click.echo("I couldn't read the textlefile from disk.")
    f.build(source_file)


@textle.command()
def live():
    if not os.path.exists(textlefile_path):
        click.echo("There isn't a project here!", err=True)
        sys.exit(1)
    try:
        with open(textlefile_path, "r") as f_:
            f = textlefile.textlefile_from_string(f_.read(), root_dir).with_job_callback(build_message_handler)
    except IOError:
        click.echo("I couldn't read the textlefile from disk.")
    observer = Observer()
    observer.schedule(f, f.root_dir, recursive=True)
    observer.start()
    click.echo("Monitoring for changes.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
