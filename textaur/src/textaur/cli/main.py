import click
from ..core.context import Context, modes
from ..core.pipeline import Pipeline
import asyncio


@click.command()
@click.argument("input_file", type=click.Path(exists=True, readable=True))
@click.option("-o", "--output", type=click.Path(), help="Save linted output to this file instead of default")
@click.option(
    "--extracted-text", type=click.Path(), help="Save extracted unlinted text to this file instead of default"
)
@click.option(
    "--ocr",
    is_flag=True,
    help="Use optical character recognition to extract text from pdf instead of direct text extraction",
)
@click.option("--no-lint", is_flag=True, help="Extract and save text without linting")
@click.option("-m", "--mode", type=click.Choice(modes, case_sensitive=False), help="Type of input text")
@click.option("--prompt", type=click.Path(exists=True, readable=True), help="File to use as custom ai linting prompt")
def main(input_file, output, extracted_text, ocr, no_lint, mode, prompt):
    try:
        context = Context(
            input_file=input_file,
            output_path=output,
            extracted_text_path=extracted_text,
            use_ocr=ocr,
            no_lint=no_lint,
            mode=mode,
            custom_prompt_path=prompt,
            log=click.echo,
            confirm=click.confirm,
            progress_fn=lambda msg: click.echo(msg, nl=False),
        )
        asyncio.run(main_async(context))
    except Exception as e:
        click.echo(f"Encountered an unexpected error:\n{e}")


async def main_async(context: Context) -> None:
    if not context.is_valid_context():
        click.echo("Setup is invalid! Aborting.")
        return
    pipeline = Pipeline(
        log=click.echo,
        progress_fn=lambda msg: click.echo(msg, nl=False),
    )
    await pipeline.run(context)
