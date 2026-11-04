from bs4 import BeautifulSoup, NavigableString
import statistics


class TextUnits:
    def __init__(self, soup, end_node_func):
        self.units = soup(end_node_func)
        self.end_node_func = end_node_func

    def tag_filter(self, tagname: str) -> list:
        if tagname == "all":
            return self.units
        filtered = filter(lambda unit: unit.name == tagname, self.units)
        return list(filtered)

    def tag_count(self, tagname: str) -> int:
        filtered = self.tag_filter(tagname)
        return len(list(filtered))

    def text_counts(self, tagname: str) -> list:
        filtered = self.tag_filter(tagname)
        return [len(unit.text.split()) for unit in filtered]

    def text_total(self, tagname: str) -> list:
        return sum(self.text_counts(tagname))

    def text_stats(self, stats, tagname: str) -> float:
        return getattr(statistics, stats)(self.text_counts(tagname))


def convert_regex_check_words(list_words):
    words = "|".join(list_words)
    return "(" + words + ")"


def child_contains_navstr(children_tags):
    func = lambda child: isinstance(child.string, NavigableString)
    return map(func, children_tags)


def end_node_with_text(tag, incl_embed_navstr=True, end_nodes=["div", "li", "p"]):

    if tag.name not in end_nodes:
        return False

    nav_str_res = list(child_contains_navstr(tag.findChildren()))
    if tag.name != "div" and all(nav_str_res) and nav_str_res:
        return True if incl_embed_navstr else False

    if not " ".join(tag.text.split()):
        return False

    if len(tag(text=False)) > 0:
        return False

    return True
