import hashlib

from metext.utils import convert_to_bytes, str_from_bytes


def _extract_with_regex(
    _input,
    regex,
    validator=None,
    per_line=True,
    preprocess=None,
    postprocess=None,
    cached_values=None,
    data_kind=None,
    include_original=True,
    include_contexts=True,
    context_length=30,
):
    def create_item(value_, position_=None, original_=None, value_kind_=None, context_=None, **kwargs):
        res = {"value": value_}
        if position_ is not None:
            res.update({"position": position_})
        if original_ is not None:
            res.update({"original": original_})
        if value_kind_ is not None:
            res.update({"value_kind": value_kind_})
        if context_ is not None:
            res.update({"context": context_})
        if kwargs:
            res.update(kwargs)
        return res

    def add_update_item_to_out(item):
        h = hashlib.sha1()
        h.update(convert_to_bytes(item["value"]))
        key_ = h.hexdigest()
        if key_ not in extracted_values:
            extracted_values[key_] = item
        if "frequency" not in extracted_values[key_]:
            extracted_values[key_]["frequency"] = 0
        extracted_values[key_]["frequency"] += 1
        if "positions" not in extracted_values[key_]:
            extracted_values[key_]["positions"] = []
        if item.get("position"):
            extracted_values[key_]["positions"].append(item["position"])
        if "position" in extracted_values[key_]:
            del extracted_values[key_]["position"]
        if "contexts" not in extracted_values[key_]:
            extracted_values[key_]["contexts"] = set()
        if item.get("context"):
            extracted_values[key_]["contexts"].add(item["context"])
        if "context" in extracted_values[key_]:
            del extracted_values[key_]["context"]

    if not isinstance(_input, str):
        try:
            _input = str_from_bytes(_input)
        except:
            yield from ()

    if cached_values is None:
        cached_values = set()

    cur_pos = 0
    extracted_values = {}
    for part in _input.splitlines(keepends=True) if per_line else [_input]:
        if preprocess is not None:
            part = preprocess(part)
        for match in regex.finditer(part):
            value = match.group(0)
            if postprocess is not None:
                value = postprocess(value)
            orig_value = match.group(0) if include_original and match.group(0) != value else None
            context = None
            if include_contexts:
                context = (
                    _input[max(cur_pos + match.start(0) - context_length, 0) : cur_pos + match.start(0)]
                    + ">>>>value<<<<"
                    + _input[cur_pos + match.end(0) : cur_pos + match.end(0) + context_length]
                )
            if cached_values is not None and value in cached_values:
                add_update_item_to_out(
                    create_item(
                        value,
                        cur_pos + match.start(0),
                        orig_value,
                        value_kind_=data_kind,
                        context_=context,
                    )
                )
                continue
            try:
                if validator is not None and not validator(value):
                    continue
            except:
                continue
            add_update_item_to_out(
                create_item(
                    value,
                    cur_pos + match.start(0),
                    orig_value,
                    value_kind_=data_kind,
                    context_=context,
                )
            )

            if isinstance(cached_values, list):
                cached_values.append(value)
            if isinstance(cached_values, set):
                cached_values.add(value)
        cur_pos += len(part)
    yield from sorted(extracted_values.values(), key=lambda x: x.get("frequency"), reverse=True)
