import json
from pathlib import Path
from typing import List, Optional, cast

import click

from .generators import (
    SUPPORTED_EXTENSIONS,
    ImageSetGenerator,
    ValidationResult,
    cleanup_invalid_files,
    generate_file,
    validate_file,
)


def format_validation_result(result: ValidationResult, verbose: bool = False) -> str:
    status = "✅" if result.is_valid else "❌"
    output = f"{status} {result.message}"
    if verbose and result.details:
        details = json.dumps(result.details, indent=2)
        output += f"\n{details}"
    return output


@click.group()
@click.version_option()
def cli() -> None:
    pass


@cli.command("generate-set")
@click.argument("config_file", type=click.Path(exists=True, path_type=Path, dir_okay=False))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True, allow_dash=False),
    default=Path.cwd(),
    help="Output directory for generated images",
)
@click.option(
    "--base-image",
    "-b",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    default=None,
    help="Base image to use for generation (optional)",
)
@click.option(
    "--background-color",
    "--bg",
    default="#ffffff",
    help="Background color for generated images (if no base image)",
)
@click.option(
    "--text",
    "-t",
    default=None,
    help="Text to render on the image (if no base image)",
)
@click.option(
    "--text-color",
    "--fg",
    default="#000000",
    help="Text color for generated images (if no base image)",
)
def generate_set(
    config_file: Path,
    output_dir: Path,
    base_image: Optional[Path],
    background_color: str,
    text: Optional[str],
    text_color: str,
) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = ImageSetGenerator.generate(
            config_path=config_file,
            output_dir=output_dir,
            base_image=str(base_image) if base_image else None,
            background_color=background_color,
            text=text,
            text_color=text_color,
        )

        if generated_files:
            click.echo("\nSuccessfully generated images:")
            for filepath in generated_files:
                click.echo(f"- {filepath}")
        else:
            click.echo(
                "No images were generated. Check your configuration file.",
                err=True,
            )

    except Exception as e:
        click.echo(f"Error generating image set: {str(e)}", err=True)
        raise click.Abort() from e


@cli.command("list")
def list_extensions() -> None:
    categories = {
        "Text Files": ["txt", "md", "markdown"],
        "Code Files": ["py", "python", "sh", "bash", "js", "html", "css", "json"],
        "Documents": ["pdf", "docx", "odt", "xlsx"],
        "Images": ["jpg", "jpeg", "png", "gif", "bmp"],
        "Archives": ["zip", "tar", "tar.gz", "tgz"],
    }

    all_exts = set(SUPPORTED_EXTENSIONS())
    categorized_exts = set(ext for exts in categories.values() for ext in exts)
    uncategorized = sorted(all_exts - categorized_exts)

    if uncategorized:
        categories["Other"] = uncategorized

    click.echo("\n" + click.style("Supported File Extensions", bold=True, fg="cyan"))
    click.echo("=" * 50)

    for category, exts in categories.items():
        click.echo(f"\n{click.style(category, bold=True, fg='yellow')}:")
        for ext in sorted(exts):
            click.echo(f"  • {ext}")

    supported_exts = SUPPORTED_EXTENSIONS()
    click.echo("\n" + "-" * 50)
    click.echo(f"Total supported extensions: {len(supported_exts)}")
    click.echo("=" * 50 + "\n")
    click.echo("Tip: Use 'text2file generate --help' to see how to generate files.")


@cli.command()
@click.argument("content", required=False)
@click.argument("extensions", nargs=-1, required=False)
@click.option(
    "--content",
    "content_option",
    type=str,
    help="Content to write to the file(s)",
)
@click.option(
    "--extension",
    "-e",
    "extensions_option",
    multiple=True,
    help="File extension(s) for the generated file(s)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True, allow_dash=False),
    default=Path.cwd(),
    help="Output directory for generated files",
)
@click.option(
    "--prefix",
    "-p",
    type=str,
    default="generated",
    help="Prefix for generated filenames",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output",
)
def generate(
    content: Optional[str],
    extensions: List[str],
    content_option: Optional[str],
    extensions_option: List[str],
    output_dir: Path,
    prefix: str,
    debug: bool,
) -> None:
    final_content = content_option if content_option is not None else content
    final_extensions = list(extensions_option) if extensions_option else list(extensions)

    if not final_content:
        raise click.UsageError("Missing content. Use --content or provide it as the first argument.")

    if not final_extensions:
        raise click.UsageError("No extensions provided. Use --extension or provide them as additional arguments.")

    output_dir.mkdir(parents=True, exist_ok=True)

    if debug:
        click.echo(f"Debug: Working directory: {Path.cwd()}", err=True)
        click.echo(f"Debug: Requested extensions: {', '.join(final_extensions)}", err=True)
        click.echo(
            f"Debug: Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            err=True,
        )

    supported_exts = SUPPORTED_EXTENSIONS()

    invalid_exts = [ext for ext in final_extensions if ext.lower().lstrip(".") not in supported_exts]
    if invalid_exts:
        raise click.UsageError(
            f"Unsupported extensions: {', '.join(invalid_exts)}. "
            f"Supported extensions: {', '.join(sorted(supported_exts))}"
        )

    generated_files = []
    for ext in final_extensions:
        try:
            filepath = generate_file(final_content, ext, output_dir, prefix)
            click.echo(f"✓ Generated: {filepath}")
            generated_files.append(filepath)
        except Exception as e:
            click.echo(f"✗ Error generating {ext} file: {e}", err=True)

    if generated_files:
        click.echo("\n🎉 Successfully generated files:")
        for filepath in generated_files:
            click.echo(f"  • {filepath}")
    else:
        click.echo("No files were generated. Check for error messages above.", err=True)


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path, allow_dash=False),
    required=True,
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively validate files in subdirectories",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation results",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format",
)
def validate(path: Path, recursive: bool, verbose: bool, output_json: bool) -> None:
    if path.is_file():
        results = {str(path): validate_file(str(path))}
    else:
        results = {}
        for file_path in path.rglob("*") if recursive else path.glob("*"):
            if file_path.is_file():
                results[str(file_path)] = validate_file(str(file_path))

    if output_json:
        output = {
            file_path: {
                "is_valid": result.is_valid,
                "message": result.message,
                "details": result.details or {},
            }
            for file_path, result in results.items()
        }
        click.echo(json.dumps(output, indent=2))
    else:
        for file_path, result in results.items():
            click.echo(f"{file_path}: {format_validation_result(result, verbose)}")


@cli.command()
@click.argument(
    "path",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        allow_dash=False,
    ),
    required=True,
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively clean up files in subdirectories",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation results",
)
def cleanup(path: Path, recursive: bool, dry_run: bool, verbose: bool) -> None:
    if dry_run:
        click.echo("Dry run mode - no files will be deleted\n")

    results = cleanup_invalid_files(str(path), recursive=recursive)

    if not results:
        click.echo("No files found to validate.")
        return

    valid_files = {}
    invalid_files = {}

    for file_path, result in results.items():
        if result.is_valid:
            valid_files[file_path] = result
        else:
            invalid_files[file_path] = result

    if invalid_files:
        click.echo(
            "The following files are invalid and would be deleted:"
            if dry_run
            else "The following invalid files were deleted:"
        )
        for file_path, result in invalid_files.items():
            click.echo(f"- {file_path}: {format_validation_result(result, verbose)}")
    else:
        click.echo("No invalid files found.")

    if verbose and valid_files:
        click.echo("\nThe following files are valid:")
        for file_path, result in valid_files.items():
            click.echo(f"- {file_path}: {format_validation_result(result, verbose)}")

    click.echo("\nSummary:")
    click.echo(f"  Total files: {len(results)}")
    click.echo(f"  Valid: {len(valid_files)}")
    click.echo(f"  Invalid: {len(invalid_files)}")

    if dry_run:
        click.echo("\nRun without --dry-run to actually delete invalid files.")
    elif invalid_files:
        click.echo(f"\nSuccessfully removed {len(invalid_files)} invalid files.")
