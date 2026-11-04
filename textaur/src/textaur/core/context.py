from pathlib import Path
from typing import Optional
from enum import Enum


class Mode(str, Enum):
    TEXT = "Text"
    SCREENPLAY = "Screenplay"


parent_dir = Path(__file__).parent
LINT_SCREENPLAY_PROMPT = Path(parent_dir / "../prompts/lint_screenplay.txt")
LINT_GENERIC_TEXT_PROMPT = Path(parent_dir / "../prompts/lint_generic_text.txt")

TEXT_SHORT = "t"
TEXT = "text"
SCREENPLAY_SHORT = "sp"
SCREENPLAY = "screenplay"

modes = [TEXT_SHORT, TEXT, SCREENPLAY_SHORT, SCREENPLAY]

mode_string_to_enum_map = {
    TEXT_SHORT: Mode.TEXT,
    TEXT: Mode.TEXT,
    SCREENPLAY_SHORT: Mode.SCREENPLAY,
    SCREENPLAY: Mode.SCREENPLAY,
}

mode_to_prompt_path_map = {
    Mode.TEXT: LINT_GENERIC_TEXT_PROMPT,
    Mode.SCREENPLAY: LINT_SCREENPLAY_PROMPT,
}

DEFAULT_LINTED_SUFFIX = "_linted.txt"
DEFAULT_EXTRACTED_SUFFIX = "_extracted_text.txt"
DEFAULT_MODE = Mode.TEXT


class Context:
    def __init__(
        self,
        input_file,
        output_path,
        extracted_text_path,
        use_ocr,
        no_lint,
        mode,
        custom_prompt_path,
        progress_fn,
        log,
        confirm,
    ):
        self.log = log
        self.confirm = confirm
        self.progress_fn = progress_fn
        self.input_file = Path(input_file)
        self.output_file = self._confirmed_filename_or_none(
            output_path,
            DEFAULT_LINTED_SUFFIX,
        )
        self.extracted_text_file = self._confirmed_filename_or_none(
            extracted_text_path,
            DEFAULT_EXTRACTED_SUFFIX,
        )
        self.use_ocr = bool(use_ocr)
        self.no_lint = bool(no_lint)
        self.mode = mode_string_to_enum_map.get(mode, DEFAULT_MODE)
        self.prompt_text = self._get_prompt_text(
            provided_mode=mode_string_to_enum_map[mode] if mode else None,
            custom_prompt_path=custom_prompt_path,
            no_lint=no_lint,
        )

    def _confirmed_filename_or_none(
        self,
        provided_filename,
        default_suffix,
    ) -> Optional[Path]:
        input_filename = self.input_file.stem
        input_directory = self.input_file.parent
        val = Path(provided_filename) if provided_filename else input_directory / f"{input_filename}{default_suffix}"
        return val if self._confirm_path_writeable(val) else None

    def _confirm_path_writeable(self, path: Path) -> bool:
        if not path.is_file():
            return True
        return self.confirm(f"A file already exists at {path}. Overwrite it?")

    def _get_prompt_text(
        self,
        provided_mode: Optional[Mode],
        custom_prompt_path: Path,
        no_lint: bool,
    ) -> str:
        if no_lint and (provided_mode or custom_prompt_path):
            self.log(
                "You provided the --no-lint flag, so no linting will be performed. The mode and/or prompt you provided will be ignored."
            )
            return ""
        if provided_mode and custom_prompt_path:
            self.log(
                f"You provided the preset mode {provided_mode} and also the custom prompt file {custom_prompt_path}. Ignoring {provided_mode} mode and using the custom prompt instead."
            )
        mode = provided_mode if provided_mode else self.mode or DEFAULT_MODE
        path = custom_prompt_path if custom_prompt_path else mode_to_prompt_path_map[mode]
        with open(path, "r", encoding="utf-8") as file:
            return file.read().strip()

    def is_valid_context(self) -> bool:
        valid_prompt_text = True if self.no_lint else bool(self.prompt_text)
        req = [
            self.input_file,
            self.output_file,
            self.extracted_text_file,
            valid_prompt_text,
        ]
        return sum([bool(_) for _ in req]) == len(req)
