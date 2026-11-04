from .context import Context, Mode
from .textifier import Textifier, FileType, File
from .ai_linter import AILinter
from .strutil import Strutil


class Pipeline:
    def __init__(
        self,
        log=print,
        progress_fn=lambda msg: print(f"\r{msg}", nl=False),
    ) -> None:
        self.log = log
        self.progress_fn = progress_fn
        self.textifier = Textifier(
            log=self.log,
            progress_fn=self.progress_fn,
        )
        self.strutil = Strutil(log=self.log)
        self.ai = AILinter()

    async def run(self, context: Context) -> None:
        try:
            file = self.textifier.extract_text(file=context.input_file, use_ocr=context.use_ocr)
            if file.filetype == FileType.UNSUPPORTED or not file.filetype or not (file.text or file.pages):
                self.log("Unable to extract text. Sorry!")
                return
            if not file.filetype == FileType.TEXT:
                extracted = "".join(file.pages) if file.pages else file.text
                self.strutil.write_file(
                    path=context.extracted_text_file,
                    text=extracted,
                )
                self.log(f"Saved extracted text to: {context.extracted_text_file}")
            if context.no_lint:
                return
            chunks = self._get_chunked(context, file)
            self.log(f"AI linting in a batch of {len(chunks)} pieces. This may take a while...")
            linted_text = await self._get_linted(context, chunks)
            self.log("AI linting complete.")
            self.strutil.write_file(path=context.output_file, text=linted_text)
            self.log(f"Saved linted text to: {context.output_file}")
            self.log("Finished!")
        except Exception as e:
            self.log(f"Encountered an unexpected error:\n{e}")

    def _get_chunked(self, context: Context, file: File) -> list[str]:
        if file.pages:
            chunks = self.strutil.chunk_pages(file.pages)
        elif file.text:
            match context.mode:
                case Mode.SCREENPLAY:
                    chunk_fn = self.strutil.chunk_screenplay_text
                case _:
                    chunk_fn = self.strutil.chunk_generic_text
            chunks = chunk_fn(file.text)
        else:
            raise ValueError("Extracted text contains neither text nor pages.")
        return chunks

    async def _get_linted(self, context: Context, chunks: list[str]) -> str:
        raw_linted = await self.ai.batch_lint_texts(chunks, context.prompt_text)
        return self._clean_up_raw_linted(
            context=context,
            text="\n".join(raw_linted),
        )

    def _clean_up_raw_linted(self, context: Context, text: str) -> str:
        return self.strutil.remove_consecutive_blank_lines(text)
