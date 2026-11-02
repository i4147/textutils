from .shell_help import MV
from ..fileref import FileRef, FileUse
from ..pipeline import Step


class TeXStep(Step):
    name = "tex"

    def handles_extra_type(self, et):
        return et in ("biblatex", "glossaries")

    def __init__(self, files, subtype, options, extras):
        super().__init__(files, subtype, options, extras)
        self.has_bib = False
        self.has_glossary = False
        self.driver = "xetex" if subtype is None else subtype
        for extra in self.extras:
            if extra.name == "biblatex":
                if not extra.files:
                    msg = "Extra biblatex must have a source"
                    raise ValueError(msg)
                self.has_bib = True
                self.bib_options = extra.options
                self.bib_source = extra.files[0]
                self.bib_driver = "biber" if extra.subtype is None else extra.subtype
            if extra.name == "glossaries":
                self.has_glossary = True

    def get_input_types_valid(self):
        return ["tex"]

    def get_output_type(self):
        return "pdf"

    def get_products(self):
        return (
            super().get_products()
            + (
                [
                    FileRef(self.input.tag, "bcf", FileUse.GENERATED),
                    FileRef(self.input.tag, "bbl", FileUse.GENERATED),
                ]
                if self.has_bib
                else []
            )
            + ([FileRef(self.input.tag, "glo", FileUse.GENERATED)] if self.has_glossary else [])
        )

    def get_dependencies_for(self, product):
        pdf_output = [self.input]
        if self.has_bib:
            (pdf_output.append(FileRef(self.input.tag, "bbl", FileUse.GENERATED)),)
            pdf_output.append(self.bib_source)
        if self.has_glossary:
            pdf_output.append(FileRef(self.input.tag, "glo", FileUse.GENERATED))
        if product.ext == "pdf":
            return pdf_output
        elif product.ext == "bbl":
            return [FileRef(self.input.tag, "bcf", FileUse.GENERATED), self.bib_source]
        elif product.ext == "bcf":
            return [self.input, self.bib_source]
        elif product.ext == "glo":
            return [self.input]
        return None

    def solve_inout(self):
        pass

    def get_command_for(self, product):
        pdf = self.output
        bcf = FileRef(self.input.tag, "bcf", FileUse.GENERATED)
        bbl = FileRef(self.input.tag, "bbl", FileUse.GENERATED)
        glo = FileRef(self.input.tag, "glo", FileUse.GENERATED)
        tex_cmd = [self.driver, "-interaction=batchmode", self.input]
        if product == pdf:
            mv_cmd = [MV, FileRef(self.input.tag, "pdf", FileUse.GENERATED), pdf]
            return (tex_cmd,) + ((mv_cmd,) if pdf.tag != self.input.tag else tuple())
        elif product == bbl:
            return ([self.bib_driver, FileRef(self.input.tag, None, FileUse.GENERATED)],)
        elif product == bcf:
            return (tex_cmd,)
        elif product == glo:
            return (tex_cmd, ["makeglossaries", FileRef(self.input.tag, None, FileUse.GENERATED)])
        return None
