import json

import mwbase


def include(page, revision):
    if page.namespace != 0 or revision.model != "wikibase-item":
        return False

    item_doc = json.loads(revision.text)
    qid = item_doc.get("id", None)
    entity = mwbase.Entity.from_json(item_doc)

    if qid is None:
        return False

    return any((llink not in ("commonswiki", "specieswiki") and llink.endswith("wiki")) for llink in entity.sitelinks)
