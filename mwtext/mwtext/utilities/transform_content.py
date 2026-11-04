import json
import logging
import re
import sys

import mwapi
import mwcli
import mwcli.files
import yamlconf

from ..filter_functions import all_pages_and_revisions
from .util import get_siteinfo, is_relevant_page

logger = logging.getLogger(__name__)
REDIRECT_RE = re.compile("#redirect", re.I)


def transform_content(
    dump,
    transformer,
    include_criteria=None,
    allowed_namespaces=None,
    allowed_content_models=None,
    include_redirects=False,
    min_content_length=None,
    verbose=False,
):

    namespace_id_map = {ns.id: ns.name for ns in dump.site_info.namespaces}

    for page in dump:
        if verbose:
            sys.stderr.write(page.title + ": ")
            sys.stderr.flush()

        for revision in page:
            relevant = is_relevant_page(
                page,
                revision,
                include_criteria=include_criteria,
                allowed_namespaces=allowed_namespaces,
                allowed_content_models=allowed_content_models,
                include_redirects=include_redirects,
                min_content_length=min_content_length,
            )
            if not relevant:
                continue

            transformed_doc = transformer.transform(revision.text)
            rev_doc = revision.to_json()
            rev_doc["page"] = page.to_json()
            rev_doc["page"]["page_name"] = format_page_name(page, namespace_id_map)
            del rev_doc["text"]
            rev_doc["transformed_content"] = transformed_doc
            yield rev_doc

            if verbose:
                sys.stderr.write(".")
                sys.stderr.flush()

        if verbose:
            sys.stderr.write("\n")
            sys.stderr.flush()


def format_page_name(page, namespace_id_map):
    if page.namespace == 0:
        return page.title
    else:
        return namespace_id_map[page.namespace] + ":" + page.title


def process_args(args):
    try:
        Transformer = yamlconf.import_path(args["<content-transformer>"])
    except ImportError:
        Transformer = yamlconf.import_path("mwtext.content_transformers." + args["<content-transformer>"])
    if args["--siteinfo"] is not None:
        siteinfo = json.load(open(args["--siteinfo"]))["query"]
    else:
        logger.info("Gathering siteinfo from {0}".format(args["--wiki-host"]))
        session = mwapi.Session(args["--wiki-host"], user_agent="mwtext transform_content")
        siteinfo = get_siteinfo(session)

    kwarg_params = {}
    for kv in args["--param"]:
        key, value = process_param(kv)
        kwarg_params[key] = value

    transformer = Transformer.from_siteinfo(siteinfo, **kwarg_params)

    if args["--include"]:
        try:
            include_criteria = yamlconf.import_path(args["--include"])
        except ImportError:
            include_criteria = yamlconf.import_path("mwtext.filter_functions." + args["--include"])
    else:
        include_criteria = all_pages_and_revisions

    include_redirects = bool(args["--include-redirects"])

    if len(args["--namespace"]) == 0:
        allowed_namespaces = None
    else:
        allowed_namespaces = set(int(v) for v in args["--namespace"])

    if len(args["--content-model"]) == 0:
        allowed_content_models = None
    else:
        allowed_content_models = set(cm for cm in args["--content-model"])

    min_content_length = int(args["--min-content-length"])

    return {
        "transformer": transformer,
        "include_criteria": include_criteria,
        "include_redirects": include_redirects,
        "allowed_namespaces": allowed_namespaces,
        "allowed_content_models": allowed_content_models,
        "min_content_length": min_content_length,
    }


def process_param(kv):
    key, value_str = kv.split("=", 1)
    return key, json.loads(value_str)


streamer = mwcli.Streamer(
    __doc__,
    __name__,
    transform_content,
    process_args=process_args,
    file_reader=mwcli.Streamer.read_xml,
    line_writer=mwcli.Streamer.write_json,
)

main = streamer.main
