import typing as t
from enum import Enum
import hashlib
import json
import logging
import multiprocessing
import shutil
import tempfile
from pathlib import Path
from functools import partial

from lxml import etree as ET

try:
    import pelican
    import pelican.settings

    PELICAN_NOT_INSTALLED = False
except ImportError:
    PELICAN_NOT_INSTALLED = True

from pydantic import (
    field_validator,
    model_validator,
    ConfigDict,
    HttpUrl,
    PrivateAttr,
    ValidationInfo,
)
import pydantic_xml as pxml
from pydantic_xml.element.element import SearchMode
from .xml import Executables, LegacyProject, LatexEngine, Method, PdfMethod
from . import generate
from .. import constants
from .. import core
from .. import utils
from .. import types as pt
from .. import resources
from .. import VERSION

# from .. import logger
# log = logger.log

log = logging.getLogger("ptxlogger")


class Format(str, Enum):
    HTML = "html"
    LATEX = "latex"
    PDF = "pdf"
    EPUB = "epub"
    EPUB_NOZIP = "epub_nozip"
    KINDLE = "kindle"
    BRAILLE = "braille"
    REVEALJS = "revealjs"
    BEAMER = "beamer"
    WEBWORK = "webwork"
    CUSTOM = "custom"


_SINGLE_FILE_FORMAT_EXTENSIONS: t.Dict["Format", str] = {
    Format.PDF: ".pdf",
    Format.EPUB: ".epub",
    Format.KINDLE: ".epub",
    Format.BRAILLE: ".brl",
    Format.BEAMER: ".pdf",
}


class PublicationSubset(pxml.BaseXmlModel, tag="publication", search_mode=SearchMode.UNORDERED):
    baseurl: t.Optional[str] = pxml.wrapped("html/baseurl", pxml.attr(name="href", default=None))


class BrailleMode(str, Enum):
    EMBOSS = "emboss"
    ELECTRONIC = "electronic"


class Compression(str, Enum):
    ZIP = "zip"
    SCORM = "scorm"


class Platform(str, Enum):
    WEB = "web"
    RUNESTONE = "runestone"


class AsyMethod(str, Enum):
    LOCAL = "local"
    SERVER = "server"


class ServerName(str, Enum):
    SAGE = "sage"
    ASY = "asy"


class Server(pxml.BaseXmlModel, tag="server"):
    model_config = ConfigDict(extra="forbid")
    name: ServerName = pxml.attr()
    url: HttpUrl = pxml.attr()


class Target(pxml.BaseXmlModel, tag="target", search_mode=SearchMode.UNORDERED):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    _project: "Project" = PrivateAttr()
    name: str = pxml.attr()
    format: Format = pxml.attr()
    source: Path = pxml.attr(default=Path("main.ptx"))
    _source_element: t.Optional[ET._Element] = None
    _managed_dirs: t.Optional[t.Tuple[Path, t.Optional[Path]]] = None
    _schema_checked: bool = False
    _source_element_with_ids: t.Optional[ET._Element] = None
    publication: Path = pxml.attr(default=None)
    method: t.Optional[Method] = pxml.attr(name="method", default=None)
    latex_engine: t.Optional[LatexEngine] = pxml.attr(name="latex-engine", default=None)
    pdf_method: t.Optional[PdfMethod] = pxml.attr(name="pdf-method", default=None)
    _document_engine: LatexEngine = PrivateAttr(default=LatexEngine.XELATEX)
    latex_source: t.Optional[str] = pxml.attr(name="latex-source", default=None)

    @field_validator("latex_source")
    @classmethod
    def latex_source_validator(cls, v: t.Optional[str]) -> bool:
        if v is None:
            return False
        return v.lower() != "no"

    @model_validator(mode="after")
    def method_validator(self) -> "Target":
        legacy_engine: t.Optional[LatexEngine] = None
        if self.pdf_method is not None:
            if self.pdf_method == PdfMethod.PDF_FO:
                legacy_method = Method.FO
                replacement = 'method="fo"'
            else:
                legacy_method = Method.LATEX
                legacy_engine = LatexEngine(self.pdf_method.value)
                replacement = f'method="latex" with latex-engine="{legacy_engine.value}"'
            log.warning(
                f'Target "{self.name}" uses pdf-method="{self.pdf_method.value}", which is deprecated. '
                f"Use {replacement} instead."
            )
            if self.method is None:
                self.method = legacy_method
            elif self.method != legacy_method:
                log.warning(
                    f'Target "{self.name}" sets both method="{self.method.value}" and '
                    f'pdf-method="{self.pdf_method.value}", which disagree.  Using method="{self.method.value}".'
                )
        if self.method is None:
            self.method = Method.LATEX
        if self.latex_engine is None:
            self.latex_engine = LatexEngine.XELATEX
        self._document_engine = legacy_engine if legacy_engine is not None else self.latex_engine
        if self.method == Method.FO and self.format != Format.PDF:
            raise ValueError(
                f'Target "{self.name}" has format "{self.format.value}", which does not support '
                'method="fo".  Only format="pdf" can be built through XSL-FO.'
            )
        return self

    braille_mode: BrailleMode = pxml.attr(name="braille-mode", default=BrailleMode.EMBOSS)
    stringparams: t.Dict[str, str] = pxml.element(default={})

    deploy: t.Optional[str] = pxml.attr(name="deploy", default=None)
    deploy_dir: t.Optional[Path] = pxml.attr(name="deploy-dir", default=None)

    def to_deploy(self) -> bool:
        deploy = self.deploy
        if deploy is None:
            return self.deploy_dir is not None
        else:
            return deploy.lower() != "no"

    standalone: t.Optional[str] = pxml.attr(name="standalone", default=None)

    def is_standalone(self) -> bool:
        standalone = self.standalone
        if standalone is None:
            return False
        return standalone.lower() != "no"

    platform: t.Optional[Platform] = pxml.attr(
        default=None,
        validate_default=True,
    )

    @field_validator("platform")
    @classmethod
    def platform_validator(cls, v: t.Optional[Platform], info: ValidationInfo) -> t.Optional[Platform]:
        if info.data.get("format") == Format.HTML:
            if v is None:
                return Platform.WEB
        else:
            if v is not None:
                raise ValueError("Only the HTML format supports the platform attribute.")
        return v

    compression: t.Optional[Compression] = pxml.attr(default=None)

    @field_validator("compression")
    @classmethod
    def compression_validator(cls, v: t.Optional[Compression], info: ValidationInfo) -> t.Optional[Compression]:
        if info.data.get("format") not in (Format.HTML, Format.WEBWORK) and v is not None:
            raise ValueError("Only the HTML and WeBWorK formats support compression.")
        if info.data.get("format") == Format.HTML and info.data.get("platform") == Platform.RUNESTONE:
            raise ValueError("The HTML format for the Runestone platform does not allow compression.")
        return v

    output_dir: t.Optional[Path] = pxml.attr(
        name="output-dir",
        default=None,
        validate_default=True,
    )

    @field_validator(
        "output_dir",
        mode="before",
    )
    @classmethod
    def output_dir_validator(cls, v: t.Optional[Path], info: ValidationInfo) -> t.Optional[Path]:
        if info.data.get("format") == Format.HTML and info.data.get("platform") == Platform.RUNESTONE and v is not None:
            raise ValueError("The Runestone format's output-dir must not be specified.")
        if v is None and info.data.get("standalone") is not None and info.data.get("standalone") != "no":
            return None
        return Path(v) if v is not None else Path(info.data.get("name", "no-name-provided"))

    output_filename: t.Optional[str] = pxml.attr(name="output-filename", default=None, validate_default=True)

    @field_validator("output_filename")
    @classmethod
    def output_filename_validator(cls, v: t.Optional[str], info: ValidationInfo) -> t.Optional[str]:
        if v is not None:
            if info.data.get("format") == Format.WEBWORK and info.data.get("compression") is None:
                raise ValueError("The output-filename must not be present when the format is  Webwork.")
            if info.data.get("format") == Format.HTML and (
                info.data.get("platform") == Platform.RUNESTONE or info.data.get("compression") is None
            ):
                raise ValueError("The output-filename must not be present when the format is HTML.")

        assert v is None or Path(v).name == v
        return v

    asy_method: t.Optional[AsyMethod] = pxml.attr(name="asy-method", default=None)

    server: t.List[Server] = pxml.element(default=[])

    @field_validator("server")
    @classmethod
    def server_validator(cls, v: t.List[Server]) -> t.List[Server]:
        if len(set([server.name for server in v])) != len(v):
            raise ValueError("Server names must not be repeated.")
        return v

    xsl: t.Optional[Path] = pxml.attr(default=None)

    @field_validator("xsl")
    @classmethod
    def xsl_validator(cls, v: t.Optional[Path], info: ValidationInfo) -> t.Optional[Path]:
        if v is None and info.data.get("format") == Format.CUSTOM:
            raise ValueError("A custom format requires a value for xsl.")
        return v

    def __init__(self, **kwargs: t.Any):
        super().__init__(**kwargs)
        if "_project" in kwargs:
            self._project = kwargs["_project"]
            self.post_validate()

    def post_validate(self) -> None:
        if self.publication is None:
            self.publication = Path("publication.ptx")
            if not self.publication_abspath().exists():
                if self.is_standalone():
                    self.publication = resources.resource_base_path() / "publication.ptx"
                else:
                    self.publication = resources.resource_base_path() / "templates" / "publication.ptx"
                # with resource_base_path() / "templates" / "publication.ptx" as self.publication:
                # pass
        else:
            p_full = self.publication_abspath()
            if not p_full.exists():
                log.warning(f'The target "{self.name}" has a specified publication file that does not exist: {p_full}')
        self.asy_method = self.asy_method or self._project.asy_method

        self_server_names = [server.name for server in self.server]
        for server in self._project.server:
            if server.name not in self_server_names:
                self.server.append(server)

    def source_abspath(self) -> Path:
        return self._project.source_abspath() / self.source

    def original_source_element(self) -> ET._Element:
        source_doc = ET.parse(self.source_abspath())
        for _ in range(25):
            source_doc.xinclude()
        print("Type of source_doc: ", type(source_doc))
        return source_doc.getroot()

    def source_element(self) -> ET._Element:
        if self._source_element is None:
            log.debug(
                f"Parsing source element for target {self.name}",
            )
            self._source_element = core.assembly_internal(
                xml=self.source_abspath(),
                pub_file=self.publication_abspath().as_posix(),
                stringparams=self.stringparams.copy(),
                method="version",
            ).getroot()
        else:
            log.debug(f"Using cached source_element for target {self.name}")
        return self._source_element

    def check_schema(self) -> None:
        if self._schema_checked:
            return
        self._schema_checked = True
        utils.warn_on_schema_errors(self.source_element(), self._project.logs_abspath())

    def source_element_with_ids(self) -> ET._Element:
        if self._source_element_with_ids is None:
            log.debug(
                f"Parsing source element with assembly ids for target {self.name}",
            )
            self._source_element_with_ids = core.assembly_internal(
                xml=self.source_abspath(),
                pub_file=self.publication_abspath().as_posix(),
                stringparams=self.stringparams.copy(),
                method="assembly-id",
            ).getroot()
        else:
            log.debug(f"Using cached source_element_with_ids for target {self.name}")
        return self._source_element_with_ids

    def publication_abspath(self) -> Path:
        return self._project.publication_abspath() / self.publication

    def output_dir_abspath(self) -> Path:
        if self.is_standalone() and self.output_dir is None:
            if self.format == Format.PDF or self.compression == Compression.SCORM:
                return self.source_abspath().parent
            return self.source_abspath().parent / f"{self.source_abspath().stem}_{self.name}"
        assert self.output_dir is not None
        return self._project.output_dir_abspath() / self.output_dir

    def output_dir_relpath(self) -> Path:
        if self.output_dir is None:
            return self.output_dir_abspath()
        return self._project.output_dir / self.output_dir

    def deploy_dir_path(self) -> Path:
        if self.deploy_dir is None:
            return Path(self.name)
        return self.deploy_dir

    def deploy_dir_abspath(self) -> Path:
        return self._project.stage_abspath() / self.deploy_dir_path()

    def deploy_dir_relpath(self) -> Path:
        return self._project.stage / self.deploy_dir_path()

    def deploy_path(self) -> Path:
        if self.output_filename is not None:
            return self.deploy_dir_path() / self.output_filename
        ext = _SINGLE_FILE_FORMAT_EXTENSIONS.get(self.format)
        if ext is not None:
            output_dir = self.output_dir_abspath()
            if output_dir.exists():
                gen = output_dir.glob(f"*{ext}")
                first = next(gen, None)
                if first is not None and next(gen, None) is None:
                    return self.deploy_dir_path() / first.name
        return self.deploy_dir_path()

    def xsl_abspath(self) -> t.Optional[Path]:
        if self.xsl is None:
            return None
        return self._project.xsl_abspath() / self.xsl

    def generated_cache_abspath(self) -> Path:
        return self._project.generated_cache_abspath()

    def _read_publication_file_subset(self) -> PublicationSubset:
        p_et = ET.parse(self.publication_abspath())
        p_et.xinclude()
        p_bytes = ET.tostring(p_et)
        return PublicationSubset.from_xml(p_bytes)

    def _managed_directories(self) -> t.Tuple[Path, t.Optional[Path]]:
        if self._managed_dirs is None:
            generated, external = core.get_managed_directories(
                self.source_abspath(), self.publication_abspath().as_posix()
            )
            self._managed_dirs = (
                Path(generated).resolve(),
                None if external is None else Path(external).resolve(),
            )
        return self._managed_dirs

    def external_dir_abspath(self) -> t.Optional[Path]:
        return self._managed_directories()[1]

    def generated_dir_abspath(self) -> Path:
        return self._managed_directories()[0]

    def asset_tables(self) -> t.Tuple[t.List[str], t.Dict[str, t.List[str]]]:
        if self.method == Method.FO:
            return constants.ASSETS_BY_FORMAT_FO, dict(constants.ASSET_FORMATS_FO)
        return (
            constants.ASSETS_BY_FORMAT[self.format],
            dict(constants.ASSET_FORMATS[self.format]),
        )

    def ensure_asset_directories(self, asset: t.Optional[str] = None) -> None:
        self.generated_dir_abspath().mkdir(parents=True, exist_ok=True)
        if asset is not None:
            for asset_dir in constants.ASSET_TO_DIR[asset]:
                (self.generated_dir_abspath() / asset_dir).mkdir(parents=True, exist_ok=True)

    def ensure_output_directory(self) -> None:
        log.debug(f"Ensuring output directory for {self.name}: {self.output_dir_abspath()}")
        self.output_dir_abspath().mkdir(parents=True, exist_ok=True)

    def load_asset_table(self) -> pt.AssetTable:
        try:
            with open(self.generated_cache_abspath() / f".{self.name}_assets.json", "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def generate_asset_table(self) -> pt.AssetTable:
        asset_hash_dict: pt.AssetTable = {}
        ns = {"pf": "https://prefigure.org"}
        for asset in constants.ASSET_TO_XPATH.keys():
            source_assets = self.source_element().xpath(constants.ASSET_TO_XPATH[asset], namespaces=ns)
            assert isinstance(source_assets, t.List)
            if len(source_assets) == 0:
                continue
            # asset_hash_dict[asset] = {}
            hash = hashlib.sha256()
            for node in source_assets:
                assert isinstance(node, ET._Element)
                hash.update(ET.tostring(node))
            if asset == "qrcode":
                base_url = self._read_publication_file_subset().baseurl
                if base_url is not None:
                    hash.update(base_url.encode("utf-8"))
            asset_hash_dict[asset] = hash.hexdigest()
        return asset_hash_dict

    def save_asset_table(self, asset_table: pt.AssetTable) -> None:
        with open(self.generated_cache_abspath() / f".{self.name}_assets.json", "w") as f:
            json.dump(asset_table, f)

    def ensure_myopenmath_xml(self, clean_tmp_dirs: bool = True) -> None:
        if self.source_element().xpath(".//myopenmath/@problem"):
            mom_prob_nums = self.source_element().xpath(".//myopenmath/@problem")
            assert isinstance(mom_prob_nums, t.List)
            if not (self.generated_dir_abspath() / "problems").exists():
                log.debug("MyOpenMath directory does not exist, creating")
                (self.generated_dir_abspath() / "problems").mkdir(parents=True, exist_ok=True)
            else:
                log.debug("MyOpenMath directory exists, not creating")

            for prob_num in mom_prob_nums:
                assert isinstance(prob_num, str)
                log.debug(f"Checking for MyOpenMath problem {prob_num}")
                if not (self.generated_dir_abspath() / "problems" / f"mom-{prob_num}.xml").exists():
                    log.debug(f"MyOpenMath problem {prob_num} does not exist, generating")
                    self.generate_assets(
                        requested_asset_types=["myopenmath"],
                        only_changed=False,
                        clean_tmp_dirs=clean_tmp_dirs,
                    )
                    break
        else:
            log.debug("Source does not contain myopenmath problems")

    def ensure_webwork_reps(self, clean_tmp_dirs: bool = True) -> None:
        if self.source_element().xpath(".//webwork[@copy|@source|*|text()]"):
            log.debug("Source contains webwork problems")
            pi_ns = {"pi": "http://pretextbook.org/2020/pretext/internal"}
            webwork_assembly_ids = self.source_element_with_ids().xpath(
                ".//webwork[@copy|@source|*|text()]/parent::*/@pi:assembly-id",
                namespaces=pi_ns,
            )
            assert isinstance(webwork_assembly_ids, list)
            for id in webwork_assembly_ids:
                assert isinstance(id, str)
                filename = id + ".xml"
                if not (self.generated_dir_abspath() / "webwork" / filename).exists():
                    log.debug(
                        f'At least one WeBWorK representation file (for webwork problem with id "{id}") does not exist, generating'
                    )
                    self.generate_assets(
                        requested_asset_types=["webwork"],
                        only_changed=False,
                        clean_tmp_dirs=clean_tmp_dirs,
                    )
                    break
            else:
                log.debug("All WeBWorK representation files already exist, not generating")
        else:
            log.debug("Source does not contain webwork problems")

    def ensure_play_button(self) -> None:
        try:
            core.play_button(dest_dir=(self.generated_dir_abspath() / "play-button"))
            log.debug("Play button generated")
        except Exception as e:
            log.warning(f"Failed to generate play button: {e}")

    def clean_output(self) -> None:
        if self._project.abspath() not in self.output_dir_abspath().parents:
            log.warning("Refusing to clean output directory that isn't a proper subdirectory of the project.")
        elif not self.output_dir_abspath().exists():
            log.warning(f"Directory {self.output_dir_abspath()} already does not exist, nothing to clean.")
        else:
            log.warning(f"Destroying directory {self.output_dir_abspath()} to clean previously built files.")
            shutil.rmtree(self.output_dir_abspath())

    def clean_assets(self) -> None:
        for asset_dir in [self.generated_dir_abspath(), self.generated_cache_abspath()]:
            if self._project.abspath() not in asset_dir.parents:
                log.warning("Refusing to clean generated directory that isn't a proper subdirectory of the project.")
            elif not asset_dir.exists():
                log.warning(f"Directory {asset_dir} already does not exist, nothing to clean.")
            else:
                log.warning(f"Destroying directory {asset_dir} to clean previously built assets.")
                shutil.rmtree(asset_dir)

    def build_theme(self) -> None:
        if self.format != Format.HTML:
            log.warning(f"Theme building is only supported for HTML targets, not {self.format}.")
            return
        log.info(f"Building theme for target '{self.name}'")
        utils.ensure_css_node_modules()
        pub_vars = core.get_publisher_variable_report(
            self.source_abspath(),
            self.publication_abspath().as_posix(),
            self.stringparams,
        )
        core.build_or_copy_theme(
            xml=self.source_abspath(),
            pub_var_dict=pub_vars,
            tmp_dir=self.output_dir_abspath().as_posix(),
        )
        log.info(f"Theme built for target '{self.name}'")

    def validate_source(
        self,
        method: str = "local",
        dest_dir: t.Optional[Path] = None,
        engine: str = "jing",
        report_form: str = "full",
    ) -> t.Optional[t.Tuple[int, int, Path]]:
        if dest_dir is None:
            dest_dir = self._project.logs_abspath()
        dest_dir.mkdir(parents=True, exist_ok=True)

        overrides = None
        if engine == "salve":
            salve_command = utils.salve_shim_command()
            if salve_command is None:
                return None
            overrides = {"jing": " ".join(salve_command)}
            self._project.init_core(overrides)
        try:
            core.validate(
                xml_source=self.source_abspath(),
                pub_file=self.publication_abspath().as_posix(),
                stringparams=self.stringparams.copy(),
                out_file=None,
                dest_dir=dest_dir.as_posix(),
                method=method,
                report_form=report_form,
            )
        except OSError as e:
            log.debug(f"Validation could not run: {e}")
            return None
        finally:
            if overrides is not None:
                self._project.init_core()
        report = dest_dir / (self.source_abspath().stem + "-validation.txt")
        if not report.exists():
            return None
        lines = report.read_text(encoding="utf-8").splitlines()
        checks: t.List[str] = []
        if report_form == "terse":
            for line in lines:
                if not line.strip():
                    continue
                fields = line.split("\t")
                checks.append(fields[3] if len(fields) > 3 else "schema")
        else:
            banner = "=" * 70
            first_section = lines.index(banner) if banner in lines else 0
            prefix = "    check: "
            checks = [line[len(prefix) :].strip() for line in lines[first_section:] if line.startswith(prefix)]
        experimental = checks.count("experimental")
        return len(checks) - experimental, experimental, report

    def build(
        self,
        clean: bool = False,
        generate: bool = True,
        xmlid: t.Optional[str] = None,
        no_knowls: bool = False,
        latex: bool = False,
        clean_tmp_dirs: bool = True,
    ) -> None:
        self.stringparams["cli.version"] = VERSION[: VERSION.rfind(".")]

        try:
            self.source_element()
        except Exception as e:
            log.error(f"Error assembling source file: {e}")
            raise RuntimeError("XML syntax for source file is invalid")
        if not utils.xml_syntax_is_valid(self.publication_abspath(), "publication"):
            raise RuntimeError("XML syntax for publication file is invalid")
        self.check_schema()

        if clean:
            self.clean_output()

        self.ensure_asset_directories()

        self.ensure_webwork_reps(clean_tmp_dirs=clean_tmp_dirs)

        if generate:
            self.generate_assets(xmlid=xmlid, clean_tmp_dirs=clean_tmp_dirs)

        self.ensure_output_directory()

        if no_knowls:
            self.stringparams["debug.skip-knowls"] = "yes"

        with tempfile.TemporaryDirectory(prefix="ptxcli_") as tmp_xsl_str:
            tmp_xsl_path = Path(tmp_xsl_str) / "cli_xsl"
            if (txp := self.xsl_abspath()) is not None:
                log.info(f"Building with custom xsl {txp}")
                utils.copy_custom_xsl(txp, tmp_xsl_path)
                custom_xsl = tmp_xsl_path / txp.name
            else:
                custom_xsl = None

            if "publisher" in self.stringparams:
                log.warning(
                    "You specified a publication file via a stringparam. "
                    + "This is ignored in favor of the publication file given by the "
                    + "`publication` element in the project manifest."
                )

            log.info(f"Preparing to build into {self.output_dir_abspath()}.")
            out_file = (
                (self.output_dir_abspath() / self.output_filename).as_posix()
                if self.output_filename is not None
                else None
            )
            stringparams_copy = self.stringparams.copy()
            if self.format == Format.HTML:
                if self.platform == Platform.RUNESTONE:
                    assert self.compression is None
                    assert self.output_filename is None
                    stringparams_copy.update({"host-platform": "runestone"})
                    if core.get_platform_host(self.publication_abspath().as_posix()) != "runestone":
                        log.warning(
                            "The platform host in the publication file is not set to runestone. Since the requested target has @platform='runestone', we will override the publication file's platform host."
                        )
                utils.ensure_css_node_modules()
                core.html(
                    xml=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    file_format=self.compression or "html",
                    extra_xsl=custom_xsl,
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    ext_rs_methods=utils.rs_methods,
                )
            elif self.format == Format.PDF:
                if self.method == Method.FO:
                    if custom_xsl is not None:
                        log.warning(
                            "Custom XSL is not supported by the XSL-FO route to a PDF, "
                            f'so the "xsl" setting of target "{self.name}" will be ignored.'
                        )
                    utils.mjsre_npm_install()
                    core.pdf_fo(
                        xml=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        out_file=out_file,
                        dest_dir=self.output_dir_abspath().as_posix(),
                    )
                else:
                    if self.latex_source:
                        latex = True
                    core.pdf(
                        xml=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        extra_xsl=custom_xsl,
                        out_file=out_file,
                        dest_dir=self.output_dir_abspath().as_posix(),
                        method=self._document_engine,
                        outputs="all" if latex else "pdf-only",
                        latex_format="latex",
                    )
            elif self.format == Format.LATEX:
                core.pdf(
                    xml=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    extra_xsl=custom_xsl,
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    method=self._document_engine,
                    outputs="prebuild",
                    latex_format="latex",
                )
            elif self.format == Format.EPUB:
                utils.mjsre_npm_install()
                core.epub(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    file_format="epub",
                    math_format="svg",
                    stringparams=stringparams_copy,
                )
            elif self.format == Format.EPUB_NOZIP:
                utils.mjsre_npm_install()
                core.epub(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    file_format="nozip",
                    math_format="svg",
                    stringparams=stringparams_copy,
                )
            elif self.format == Format.KINDLE:
                utils.mjsre_npm_install()
                core.epub(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    file_format="epub",
                    math_format="kindle",
                    stringparams=stringparams_copy,
                )
            elif self.format == Format.REVEALJS:
                core.revealjs(
                    xml=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    file_format=None,
                    extra_xsl=custom_xsl,
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                )
            elif self.format == Format.BEAMER:
                core.pdf(
                    xml=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    extra_xsl=custom_xsl,
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    method=self._document_engine,
                    outputs="all" if latex else "pdf-only",
                    latex_format="beamer",
                )
            elif self.format == Format.BRAILLE:
                log.warning(
                    "Braille output is still experimental, and requires additional libraries from liblouis (specifically the file2brl software)."
                )
                utils.mjsre_npm_install()
                core.braille(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    out_file=out_file,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    page_format=self.braille_mode,
                    stringparams=stringparams_copy,
                )
            elif self.format == Format.WEBWORK:
                core.webwork_sets(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    dest_dir=self.output_dir_abspath().as_posix(),
                    tgz=self.compression,
                    need_macros=True,
                )
            elif self.format == Format.CUSTOM:
                stringparams_copy["publisher"] = self.publication_abspath().as_posix()
                core.xsltproc(
                    xsl=custom_xsl,
                    xml=self.source_abspath(),
                    result=out_file,
                    output_dir=self.output_dir_abspath().as_posix(),
                    stringparams=stringparams_copy,
                )
                utils.manage_directories(
                    self.output_dir_abspath(),
                    external_abs=self.external_dir_abspath(),
                    generated_abs=self.generated_dir_abspath(),
                )
            else:
                log.critical(f"Unknown format {self.format}")
        try:
            core.release_temporary_directories(any_log_level=clean_tmp_dirs)
        except Exception as e:
            log.error("Unable to release temporary directories.  Please report this error to pretext-support")
            log.debug(e, exc_info=True)

    def generate_assets(
        self,
        requested_asset_types: t.Optional[t.List[str]] = None,
        all_formats: bool = False,
        only_changed: bool = True,
        xmlid: t.Optional[str] = None,
        clean: bool = False,
        skip_cache: bool = False,
        slow: bool = False,
        clean_tmp_dirs: bool = True,
    ) -> None:
        log.info("Generating any needed assets.")

        self.check_schema()

        if requested_asset_types == ("references",):
            try:
                core.references(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=self.stringparams.copy(),
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "references",
                )
            except Exception as e:
                log.error(f"Unable to generate some references:\n {e}")
                log.debug(e, exc_info=True)
            finally:
                return
        if requested_asset_types == ("stack",):
            try:
                core.stack_extraction(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=self.stringparams.copy(),
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "stack",
                )
            except Exception as e:
                log.error(f"Unable to generate some stack assets:\n {e}")
                log.debug(e, exc_info=True)
            finally:
                return

        if clean:
            self.clean_assets()

        for subdir in ["latex-image", "asymptote", "sageplot", "prefigure"]:
            if not (self.generated_cache_abspath() / subdir).exists():
                (self.generated_cache_abspath() / subdir).mkdir(parents=True, exist_ok=True)
        log.debug(f"Using cached assets in {self.generated_cache_abspath()} where possible.")
        if requested_asset_types != ["webwork"]:
            log.debug("Ensuring webwork representations file is present.")
            self.ensure_webwork_reps()
            if requested_asset_types != ["myopenmath"]:
                log.debug("Ensuring MyOpenMath XML files are present.")
                self.ensure_myopenmath_xml()

        if requested_asset_types is None or "ALL" in requested_asset_types:
            requested_asset_types = list(constants.ASSET_TO_XPATH.keys())
        log.debug(f"Assets generation requested for: {requested_asset_types}.")
        assets_by_format, asset_formats = self.asset_tables()
        requested_asset_types = [asset for asset in requested_asset_types if asset in assets_by_format]
        log.debug(f"Based on format {self.format}, assets to be generated are: {requested_asset_types}.")
        source_asset_table = self.generate_asset_table()
        saved_asset_table = utils.clean_asset_table(self.load_asset_table(), source_asset_table)
        # log.debug(f"Starting asset table: {source_asset_table}")
        source_asset_table = {
            asset: source_asset_table[asset] for asset in source_asset_table if asset in requested_asset_types
        }
        requested_asset_types = [asset for asset in source_asset_table]
        log.debug(f"Based on what is in your source, the assets that will be considered are {requested_asset_types}.")

        assets_to_generate = []
        if only_changed:
            for asset in requested_asset_types:
                if asset not in saved_asset_table or saved_asset_table[asset] != source_asset_table[asset]:
                    assets_to_generate.append(asset)
        else:
            assets_to_generate = requested_asset_types
        log.debug(f"Assets to be generated: {assets_to_generate}")

        for asset in assets_to_generate:
            self.ensure_asset_directories(asset)

        if all_formats:
            for asset in assets_to_generate:
                asset_formats[asset] = ["all"]

        successful_assets: t.List[str] = []
        stringparams_copy = self.stringparams.copy()
        if "webwork" in assets_to_generate:
            try:
                core.webwork_to_xml(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    abort_early=False,
                    dest_dir=(self.generated_dir_abspath() / "webwork").as_posix(),
                    server_params=None,
                )
                successful_assets.append("webwork")
            except Exception as e:
                log.error(
                    "Unable to generate webwork.  If you already have a webwork-representations.xml file, this might result in unpredictable behavior."
                )
                log.warning(e)
                log.debug(e, exc_info=True)
        if "myopenmath" in assets_to_generate:
            try:
                core.mom_static_problems(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=(self.generated_dir_abspath() / "problems").as_posix(),
                )
                successful_assets.append("myopenmath")
            except Exception as e:
                log.error("Unable to generate MyOpenMath static files.")
                log.warning(e)
                log.debug(e, exc_info=True)
        if "dynamic-subs" in assets_to_generate:
            try:
                utils.ensure_dynsub_node_modules()
                core.dynamic_substitutions(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "dynamic_subs",
                    ext_rs_methods=utils.rs_methods,
                )
                successful_assets.append("dynamic-subs")
            except Exception as e:
                log.error(f"Unable to extract some dynamic exercise substitutions: \n{e}")
                log.debug(e, exc_info=True)
        if "qrcode" in assets_to_generate:
            log.warning("Now generating QR codes")
            try:
                base_url = self._read_publication_file_subset().baseurl
                if base_url is None:
                    log.warning(
                        "You are trying to generate qrcodes, but the publication file does not have a base URL. "
                        + "This will result in qrcodes that do not point to anything meaningful."
                    )
                core.qrcode(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "qrcode",
                )
                successful_assets.append("qrcode")
            except Exception as e:
                log.error(f"Unable to generate some qrcodes:\n {e}")
                log.debug(e, exc_info=True)
        if "latex-image" in assets_to_generate:
            log.warning("Now generating latex images")
            try:
                for outformat in asset_formats["latex-image"]:
                    core.latex_image_conversion(
                        xml_source=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        xmlid_root=xmlid,
                        dest_dir=self.generated_dir_abspath() / "latex-image",
                        outformat=outformat,
                        method=self.latex_engine,
                        ext_converter=partial(
                            generate.individual_latex_image,
                            cache_dir=self.generated_cache_abspath(),
                            skip_cache=skip_cache,
                        ),
                    )
                successful_assets.append("latex-image")
            except Exception as e:
                log.error(f"Unable to generate some latex-image assets:\n {e}")
                log.debug(e, exc_info=True)
        if "asymptote" in assets_to_generate:
            try:
                for outformat in asset_formats["asymptote"]:
                    core.asymptote_conversion(
                        xml_source=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        xmlid_root=xmlid,
                        dest_dir=self.generated_dir_abspath() / "asymptote",
                        outformat=outformat,
                        method=self.asy_method,
                        ext_converter=partial(
                            generate.individual_asymptote,
                            cache_dir=self.generated_cache_abspath(),
                            skip_cache=skip_cache,
                        ),
                    )
                successful_assets.append("asymptote")
            except Exception as e:
                log.error(f"Unable to generate some asymptote elements: \n{e}")
                log.debug(e, exc_info=True)
        if "sageplot" in assets_to_generate:
            try:
                for outformat in asset_formats["sageplot"]:
                    core.sage_conversion(
                        xml_source=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        xmlid_root=xmlid,
                        dest_dir=self.generated_dir_abspath() / "sageplot",
                        outformat=outformat,
                        ext_converter=partial(
                            generate.individual_sage,
                            cache_dir=self.generated_cache_abspath(),
                            skip_cache=skip_cache,
                        ),
                    )
                successful_assets.append("sageplot")
            except Exception as e:
                log.error(f"Unable to generate some sageplot images:\n {e}")
                log.debug(e, exc_info=True)
        if "prefigure" in assets_to_generate:
            try:
                for outformat in asset_formats["prefigure"]:
                    core.prefigure_conversion(
                        xml_source=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        xmlid_root=xmlid,
                        dest_dir=self.generated_dir_abspath() / "prefigure",
                        outformat=outformat,
                        ext_converter=partial(
                            generate.individual_prefigure,
                            cache_dir=self.generated_cache_abspath(),
                            skip_cache=skip_cache,
                        ),
                    )
                successful_assets.append("prefigure")
            except Exception as e:
                log.error(f"Unable to generate some prefigure images:\n {e}")
                log.debug(e, exc_info=True)
        if "interactive" in assets_to_generate:
            try:
                utils.playwright_install()
                core.preview_images(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "preview",
                    method="slow" if slow else "fast",
                )
                successful_assets.append("interactive")
            except Exception as e:
                log.error(f"Unable to generate some interactive previews: \n{e}")
                log.debug(e, exc_info=True)
        if "youtube" in assets_to_generate:
            try:
                core.youtube_thumbnail(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "youtube",
                )
                successful_assets.append("youtube")
            except Exception as e:
                log.error(f"Unable to generate some youtube thumbnails: \n{e}")
                log.debug(e, exc_info=True)
            self.ensure_play_button()
        if "gdscript" in assets_to_generate:
            try:
                core.gdscript_pck(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "gdscript",
                )
                successful_assets.append("gdscript")
            except Exception as e:
                log.error(f"Unable to generate some GDScript pck archives:\n {e}")
                log.debug(e, exc_info=True)

        if "mermaid" in assets_to_generate:
            try:
                for outformat in asset_formats["mermaid"]:
                    core.mermaid_images(
                        xml_source=self.source_abspath(),
                        pub_file=self.publication_abspath().as_posix(),
                        stringparams=stringparams_copy,
                        xmlid_root=xmlid,
                        dest_dir=self.generated_dir_abspath() / "mermaid",
                        outformat=outformat,
                    )
                    successful_assets.append("mermaid")
            except Exception as e:
                log.error(f"Unable to generate some mermaid images: \n{e}")
                log.debug(e, exc_info=True)
        if "codelens" in assets_to_generate:
            try:
                core.tracer(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "trace",
                )
                successful_assets.append("codelens")
            except Exception as e:
                log.error(f"Unable to generate some codelens traces: \n{e}")
                log.debug(e, exc_info=True)
        if "datafile" in assets_to_generate:
            try:
                core.datafiles_to_xml(
                    xml_source=self.source_abspath(),
                    pub_file=self.publication_abspath().as_posix(),
                    stringparams=stringparams_copy,
                    xmlid_root=xmlid,
                    dest_dir=self.generated_dir_abspath() / "datafile",
                )
                successful_assets.append("datafile")
            except Exception as e:
                log.error(f"Unable to generate some datafiles:\n {e}")
                log.debug(e, exc_info=True)
        # if "references" in assets_to_generate and debug_references:
        #    try:
        #        core.references(
        #            xml_source=self.source_abspath(),
        #            pub_file=self.publication_abspath().as_posix(),
        #            stringparams=stringparams_copy,
        #            xmlid_root=xmlid,
        #            dest_dir=self.generated_dir_abspath() / "references",
        #        )
        #        successful_assets.append("references")
        #    except Exception as e:
        #        log.error(f"Unable to generate some references:\n {e}")
        #        log.debug(e, exc_info=True)
        try:
            core.release_temporary_directories(any_log_level=clean_tmp_dirs)
        except Exception as e:
            log.debug("Unable to release temporary directories.")
            log.debug(e, exc_info=True)
        log.debug(f"Updated these assets successfully: {successful_assets}")
        unsuccessful_assets = [asset for asset in assets_to_generate if asset not in successful_assets]
        log.debug(f"These assets were unsuccessful: {unsuccessful_assets}")
        if not xmlid:
            for asset_type in successful_assets:
                saved_asset_table[asset_type] = source_asset_table[asset_type]
            for asset_type in unsuccessful_assets:
                log.debug(
                    f"Asset type {asset_type} was requested to be generated, but was not generated successfully.  This asset type will be regenerated on the next build, even if the source files have not changed, since we can't be sure that the existing generated assets are up to date."
                )
                saved_asset_table.pop(asset_type, None)
            self.save_asset_table(saved_asset_table)
        log.info("Finished generating assets.\n")


class Project(pxml.BaseXmlModel, tag="project", search_mode=SearchMode.UNORDERED):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    ptx_version: t.Literal["2"] = pxml.attr(name="ptx-version", default="2")
    _executables: Executables
    source: Path = pxml.attr(default=Path("source"))
    _path: Path = PrivateAttr(default=Path("."))

    @classmethod
    def validate_path(cls, path: t.Union[Path, str]) -> Path:
        path = Path(path).resolve()
        return path / "project.ptx" if path.is_dir() else path

    publication: Path = pxml.attr(default=Path("publication"))
    output_dir: Path = pxml.attr(name="output-dir", default=Path("output"))
    site: Path = pxml.attr(default=Path("site"))
    stage: Path = pxml.attr(default=Path("output/stage"))
    xsl: Path = pxml.attr(default=Path("xsl"))
    generated_cache: Path = pxml.attr(default=Path(".cache"))
    targets: t.List[Target] = pxml.wrapped("targets", pxml.element(tag="target", default=[]))

    asy_method: t.Optional[AsyMethod] = pxml.attr(name="asy-method", default=AsyMethod.LOCAL)

    server: t.List[Server] = pxml.element(default=[])

    @field_validator("server")
    @classmethod
    def server_validator(cls, v: t.List[Server]) -> t.List[Server]:
        if len(set([server.name for server in v])) != len(v):
            raise ValueError("Server names must not be repeated.")
        return v

    cname: t.Optional[str] = pxml.attr(default=None)

    @model_validator(mode="after")
    def set_metadata(self, info: ValidationInfo) -> "Project":
        c = info.context
        p = c and c.get("_path")
        if p:
            self._path = p

        try:
            e_bytes = (self._path.parent / "executables.ptx").read_bytes()
        except FileNotFoundError:
            self._executables = Executables()
        else:
            self._executables = Executables.from_xml(e_bytes)

        return self

    def __init__(self, **kwargs: t.Any):
        deferred = {}
        for key in ("_path", "_executables"):
            if key in kwargs:
                deferred[key] = kwargs.pop(key)

        super().__init__(**kwargs)

        for key, value in deferred.items():
            setattr(self, key, value)
        self._path = self.validate_path(self._path)

        self.init_core()

    @classmethod
    def parse(
        cls,
        path: t.Union[Path, str] = Path("."),
        global_manifest: bool = False,
    ) -> "Project":
        _path = cls.validate_path(path)
        xml_bytes = _path.read_bytes()

        if global_manifest:
            _path = cls.validate_path(Path("."))

        class ProjectVersionOnly(pxml.BaseXmlModel, tag="project"):
            ptx_version: t.Optional[str] = pxml.attr(name="ptx-version", default=None)

        p_version_only = ProjectVersionOnly.from_xml(xml_bytes)
        if p_version_only.ptx_version is not None:
            p = Project.from_xml(xml_bytes, context={"_path": _path})
        else:
            legacy_project = LegacyProject.from_xml(_path.read_bytes())
            new_targets: t.List[Target] = []
            for tgt in legacy_project.targets:
                compression: t.Optional[Compression] = None
                braille_mode: t.Optional[BrailleMode] = None
                if tgt.format == "html-zip":
                    format = Format.HTML
                    compression = Compression.ZIP
                elif tgt.format == "webwork-sets":
                    format = Format.WEBWORK
                elif tgt.format == "webwork-sets-zipped":
                    format = Format.WEBWORK
                    compression = Compression.ZIP
                elif tgt.format == "braille-electronic":
                    format = Format.BRAILLE
                    braille_mode = BrailleMode.ELECTRONIC
                elif tgt.format == "braille-emboss":
                    format = Format.BRAILLE
                    braille_mode = BrailleMode.EMBOSS
                else:
                    format = Format(tgt.format.value)
                d = tgt.model_dump()
                del d["format"]

                if not Path(tgt.publication).exists():
                    log.warning(f"Publication file at {tgt.publication} does not exist.")
                    log.warning(f"{tgt.name} will not be available.")
                    continue

                for key in ("deploy_dir", "xsl", "latex_engine"):
                    if d[key] is None:
                        del d[key]

                if braille_mode is not None:
                    d["braille_mode"] = braille_mode

                d["stringparams"] = {
                    old_stringparam["key"]: old_stringparam["value"] for old_stringparam in d["stringparams"]
                }
                new_target = Target(
                    format=format,
                    compression=compression,
                    **d,
                )
                new_targets.append(new_target)

            d = legacy_project.model_dump()
            d["targets"] = new_targets
            d["_executables"] = Executables.from_legacy(legacy_project.executables)
            d.pop("executables")
            p = Project(
                ptx_version="2",
                _path=_path,
                publication=Path(""),
                source=Path(""),
                output_dir=Path(""),
                site=Path(""),
                xsl=Path(""),
                **d,
            )

        for _tgt in p.targets:
            _tgt._project = p
            _tgt.post_validate()
        # if global_manifest:
        #    p._path = Path(".")
        return p

    def new_target(self, name: str, format: t.Union[str, Format], **kwargs: t.Any) -> Target:
        t = Target(name=name, format=Format(format), **kwargs)
        t._project = self
        t.post_validate()
        self.targets.append(t)
        return t

    def _get_target(
        self,
        name: t.Optional[str] = None,
    ) -> t.Optional["Target"]:
        if len(self.targets) == 0:
            return None
        if name is None:
            return self.targets[0]
        try:
            return next(t for t in self.targets if t.name == name)
        except StopIteration:
            for target in self.targets:
                if target.format == name:
                    true_name = target.name
                    log.warning(
                        f"Could not find a target '{name}', but found a target '{true_name}' with format='{name}'; using this target."
                    )
                    return target
            return None

    def has_target(
        self,
        name: t.Optional[str] = None,
    ) -> bool:
        return self._get_target(name) is not None

    def get_target(
        self,
        name: t.Optional[str] = None,
        log_info_for_none: bool = True,
    ) -> "Target":
        t = self._get_target(name)
        assert t is not None
        if name is None and log_info_for_none:
            log.info(f'Since no target was supplied, we will use "{t.name}".\n')
        return t

    def target_names(self, *args: str) -> t.List[str]:
        names = []
        for target in self.targets:
            if not args or target.format in args:
                names.append(target.name)
        return names

    def abspath(self) -> Path:
        return self._path.parent

    def source_abspath(self) -> Path:
        return self.abspath() / self.source

    def publication_abspath(self) -> Path:
        return self.abspath() / self.publication

    def generated_cache_abspath(self) -> Path:
        return self.abspath() / self.generated_cache

    def output_dir_abspath(self) -> Path:
        return self.abspath() / self.output_dir

    def stage_abspath(self) -> Path:
        return self.abspath() / self.stage

    def site_abspath(self) -> Path:
        return self.abspath() / self.site

    def logs_abspath(self) -> Path:
        return self.abspath() / "logs"

    def deploy_strategy(
        self,
    ) -> t.Literal["default_target", "pelican_default", "pelican_custom", "static"]:
        if len(self.deploy_targets()) == 0:
            return "default_target"
        if not self.site_abspath().exists():
            return "pelican_default"
        if (self.site_abspath() / "site.ptx").exists() or (self.site_abspath() / "site.json").exists():
            return "pelican_custom"
        return "static"

    def xsl_abspath(self) -> Path:
        return self.abspath() / self.xsl

    def server_process(
        self,
        access: t.Literal["public", "private"] = "private",
        port: int = 8128,
    ) -> multiprocessing.Process:
        return multiprocessing.Process(
            target=utils.serve_forever,
            args=[self.abspath(), access, port],
        )

    def get_executables(self) -> Executables:
        return self._executables

    def init_core(self, executable_overrides: t.Optional[t.Dict[str, str]] = None) -> None:
        exec_dict = self._executables.model_dump()
        if executable_overrides is not None:
            exec_dict.update(executable_overrides)
        for k in exec_dict:
            if exec_dict[k] is None:
                exec_dict[k] = "None"
        core.set_executables(exec_dict)

    def deploy_targets(self) -> t.List[Target]:
        return [tgt for tgt in self.targets if tgt.to_deploy()]

    def standalone_targets(self) -> t.List[Target]:
        return [tgt for tgt in self.targets if tgt.is_standalone()]

    def stage_deployment(self) -> None:
        if self.stage_abspath().exists() and self.abspath() in self.stage_abspath().parents:
            shutil.rmtree(self.stage_abspath())
            log.debug("Removed old stage directory")

        self.stage_abspath().mkdir(parents=True, exist_ok=True)

        strategy = self.deploy_strategy()

        log.info(f"Staging deployment according to strategy {strategy}")

        if strategy == "default_target":
            target = self.get_target()
            if target is None:
                log.error("Target not found.")
                return
            if not target.output_dir_abspath().exists():
                log.error(f"No build for `{target.name}` was found in the directory `{target.output_dir_abspath()}`.")
                log.error(f"Try running `pretext build {target.name}` to build your project first.")
                return
            log.info(f"Staging latest build located in `{target.output_dir_abspath()}` at `{self.stage_abspath()}`.")
            log.info("")
            shutil.copytree(
                target.output_dir_abspath(),
                self.stage_abspath(),
                dirs_exist_ok=True,
            )
        else:
            for target in self.deploy_targets():
                if not target.output_dir_abspath().exists():
                    log.warning(
                        f"No build for `{target.name}` was found in the directory `{target.output_dir_abspath()}`."
                        + f"Try running `pretext build {target.name}` to build this component first."
                    )
                    log.info("Skipping this target for now.")
                else:
                    shutil.copytree(
                        target.output_dir_abspath(),
                        target.deploy_dir_abspath(),
                        dirs_exist_ok=True,
                    )
                    log.info(f"Staging `{target.name}` at `{target.deploy_dir_abspath()}`.")
            if strategy == "static":
                log.info(f"Staging custom static site located in `{self.site.resolve()}` at `{self.stage_abspath()}`.")
                shutil.copytree(
                    self.site.resolve(),
                    self.stage_abspath(),
                    dirs_exist_ok=True,
                )
            else:
                if PELICAN_NOT_INSTALLED:
                    log.error("Pelican is not installed. Please install Pelican to use this feature.")
                    return
                if strategy == "pelican_custom":
                    log.warning("Support for customizing websites generated by PreTeXt-CLI is experimental!")
                    log.warning("Configurations are subject to change from version-to-version without notice.")
                    log.warning("Discussion: https://github.com/PreTeXtBook/pretext-cli/discussions/766")
                with tempfile.TemporaryDirectory(prefix="ptxcli_") as tmp_dir_str:
                    log.info(f"Staging generated site at `{self.stage_abspath()}`.")
                    config = utils.pelican_default_settings()
                    config["OUTPUT_PATH"] = str(self.stage_abspath())
                    if strategy == "pelican_custom":
                        config["PATH"] = str(self.site_abspath())
                    else:
                        config["PATH"] = tmp_dir_str
                    root = self.deploy_targets()[0].source_element()
                    for title_ele in root.iterdescendants("title"):
                        config["SITENAME"] = title_ele.text
                        break
                    else:
                        config["SITENAME"] = "My PreTeXt Project"
                    for subtitle_ele in root.iterdescendants("subtitle"):
                        config["SITESUBTITLE"] = subtitle_ele.text
                        break
                    for blurb_ele in root.iterdescendants("blurb"):
                        config["PTX_SITE_DESCRIPTION"] = blurb_ele.text
                        break
                    config["PTX_TARGETS"] = [(t.name.capitalize(), t.deploy_path()) for t in self.deploy_targets()]
                    if strategy == "pelican_custom":
                        if (self.site_abspath() / "site.ptx").exists():
                            customization = ET.parse(self.site_abspath() / "site.ptx")
                            customization.xinclude()
                            for child in customization.getroot():
                                config[str(child.tag).upper().replace("-", "_")] = child.text
                        else:
                            with open(self.site_abspath() / "site.json") as f:
                                customization = json.load(f)
                            config = {**config, **customization}
                    pelican.Pelican(pelican.settings.configure_settings(config)).run()
            log.info(f"Deployment is now staged at `{self.stage_abspath()}`.")

    def deploy(
        self,
        update_source: bool = True,
        stage_only: bool = False,
        skip_staging: bool = False,
        no_push: bool = False,
    ) -> None:
        if not skip_staging:
            self.stage_deployment()
        if not stage_only:
            utils.publish_to_ghpages(self.stage_abspath(), update_source, no_push=no_push, cname=self.cname)

    def is_git_managed(self) -> bool:
        return (self.abspath() / ".git").exists()

    def update_boilerplate(self, backup: bool = False, force: bool = False) -> None:

        for resource in constants.PROJECT_RESOURCES:
            if resource in constants.GIT_RESOURCES and not self.is_git_managed():
                continue
            project_resource_path = (self.abspath() / constants.PROJECT_RESOURCES[resource]).resolve()
            if force:
                self.add_boilerplate(resource, backup=True)
                log.info(f"Generated resource file {resource}.")
                continue
            if not project_resource_path.exists():
                self.add_boilerplate(resource)
                log.info(f"Generated resource file {resource}.")
                continue
            if utils.is_unmodified(resource, project_resource_path.read_bytes()):
                log.info(
                    f"Resource {resource} has not changed since it was originially generated by PreTeXt, so it will be updated to the latest version."
                )
                self.add_boilerplate(resource, backup)
            else:
                log.warning(
                    f"Resource {resource} has been modified since created by PreTeXt and will not be updated.\n"
                )

        for depr_resource in constants.DEPRECATED_PROJECT_RESOURCES:
            project_resource_path = (self.abspath() / constants.DEPRECATED_PROJECT_RESOURCES[depr_resource]).resolve()
            if project_resource_path.exists():
                if utils.is_unmodified(
                    depr_resource,
                    project_resource_path.read_bytes(),
                ):
                    self.remove_boilerplate(depr_resource)
                log.warning(f"The deprecated {depr_resource} file has been deleted.")
        return

    def add_boilerplate(self, resource: str, backup: bool = False) -> None:
        if resource not in constants.PROJECT_RESOURCES:
            raise TypeError(f"{resource} is not a resource distributed with PreTeXt-CLI.")
        project_resource_path = (self.abspath() / constants.PROJECT_RESOURCES[resource]).resolve()
        if project_resource_path.exists() and backup:
            backup_resource_path = project_resource_path.parent / f"{project_resource_path.name}.bak"
            shutil.copyfile(project_resource_path, backup_resource_path)
            log.debug(f"Created a backup of the existing {resource} file at {backup_resource_path}.")
        if resource != "requirements.txt":
            resource_path = resources.resource_base_path() / "templates" / resource
            project_resource_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(resource_path, project_resource_path)
            log.debug(f"Generated `{project_resource_path}`\n")
        else:
            requirements_txt = (
                f"# This file was automatically generated with PreTeXt {VERSION}.\npretext == {VERSION}\n"
            )
            project_resource_path.write_text(requirements_txt)
            log.debug(f"Generated `{project_resource_path}`\n")
        return

    def remove_boilerplate(self, resource: str, backup: bool = True) -> None:
        if resource in constants.PROJECT_RESOURCES:
            project_resource_path = self.abspath() / constants.PROJECT_RESOURCES[resource]
        elif resource in constants.DEPRECATED_PROJECT_RESOURCES:
            project_resource_path = (self.abspath() / constants.DEPRECATED_PROJECT_RESOURCES[resource]).resolve()
        else:
            raise TypeError(f"{resource} is not a resource distributed with PreTeXt-CLI.")
        if backup:
            backup_resource_path = project_resource_path.parent / f"{project_resource_path.name}.bak"
            shutil.copyfile(project_resource_path, backup_resource_path)
            log.debug(f"Created a backup of the existing {resource} file at {backup_resource_path}.")
        project_resource_path.unlink()
        log.debug(f"Removed `{project_resource_path}`\n")
        return

    def generate_boilerplate(
        self,
        skip_unmanaged: bool = True,
        update_requirements: bool = False,
        resources: t.Optional[t.List[str]] = None,
        remove_deprecated: bool = True,
    ) -> None:
        log.error(
            "the `generate_boilerplate` method has been deprecated.  Will attempt to use `update_boilerplate` instead, but some options are inconsistent."
        )
        self.update_boilerplate(backup=True)
        return
