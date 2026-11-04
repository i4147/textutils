import hashlib
import json
import os
import pickle
import re
import warnings
from pathlib import Path
import nltk
from radtext.models.pphilter.coordinate_map import CoordinateMap


class Philter:
    def __init__(self):
        self.verbose = False
        self.folder = Path(__file__).parent
        self.config_file = self.folder / "philter_delta.json"
        if not os.path.exists(self.config_file):
            raise Exception("Filepath does not exist", self.config_file)
        self.patterns = json.loads(open(self.config_file, "r").read())
        for obj in self.patterns:
            if "filepath" in obj:
                obj["filepath"] = str(self.folder / obj["filepath"])
        self.coordinate_maps = []
        self.pos_tags = {}
        self.cleaned = {}
        self.include_map = CoordinateMap()
        self.exclude_map = CoordinateMap()
        self.full_exclude_map = {}
        self.phi_type_list = [
            "DATE",
            "Patient_Social_Security_Number",
            "Email",
            "Provider_Address_or_Location",
            "Age",
            "Name",
            "OTHER",
            "ID",
            "NAME",
            "LOCATION",
            "CONTACT",
            "AGE",
            "URL",
        ]
        self.phi_type_dict = {}
        for phi_type in self.phi_type_list:
            self.phi_type_dict[phi_type] = [CoordinateMap()]
        self.data_all_files = {}
        self.pattern_indexes = {}
        self.init_patterns()

    def get_pos(self, id, cleaned):
        if id not in self.pos_tags:
            self.pos_tags = {}
            self.pos_tags[id] = nltk.pos_tag(cleaned)
        return self.pos_tags[id]

    def get_clean(self, id, text, pre_process=r"[^a-zA-Z0-9]"):
        if id not in self.cleaned:
            self.cleaned = {}
            lst = re.split(r"(\s+)", text)
            cleaned = []
            for item in lst:
                if len(item) > 0:
                    if not item.isspace():
                        split_item = re.split(r"(\s+)", re.sub(pre_process, " ", item))
                        for elem in split_item:
                            if len(elem) > 0:
                                cleaned.append(elem)
                    else:
                        cleaned.append(item)
            self.cleaned[id] = cleaned
        return self.cleaned[id]

    def init_patterns(self):
        known_pattern_types = {"regex", "set", "regex_context", "stanford_ner", "pos_matcher", "match_all"}
        require_files = {"regex", "set"}
        set_filetypes = {"pkl", "json"}
        regex_filetypes = {"txt"}
        reserved_list = {"data", "coordinate_map"}
        for i, pattern in enumerate(self.patterns):
            self.pattern_indexes[pattern["title"]] = i
            if pattern["type"] in require_files and not os.path.exists(pattern["filepath"]):
                raise Exception("Config filepath does not exist", pattern["filepath"])
            for k in reserved_list:
                if k in pattern:
                    raise Exception("Error, Keyword is reserved", k, pattern)
            if pattern["type"] not in known_pattern_types:
                raise Exception("Pattern type is unknown", pattern["type"])
            if pattern["type"] == "set":
                if pattern["filepath"].split(".")[-1] not in set_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", set_filetypes)
                self.patterns[i]["data"] = self.init_set(pattern["filepath"])
            if pattern["type"] == "regex":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns[i]["data"] = self.precompile(pattern["filepath"])
            elif pattern["type"] == "regex_context":
                if pattern["filepath"].split(".")[-1] not in regex_filetypes:
                    raise Exception("Invalid filteype", pattern["filepath"], "must be of", regex_filetypes)
                self.patterns[i]["data"] = self.precompile(pattern["filepath"])

    def precompile(self, filepath):
        regex = open(filepath, "r").read().strip()
        with warnings.catch_warnings():
            warnings.simplefilter(action="error", category=FutureWarning)
            try:
                re_compiled = re.compile(regex)
            except FutureWarning as warn:
                print("FutureWarning: {0} in file ".format(warn) + filepath)
                warnings.simplefilter(action="ignore", category=FutureWarning)
                re_compiled = re.compile(regex)
                pass
        return re_compiled

    def init_set(self, filepath):
        if filepath.endswith(".pkl"):
            try:
                with open(filepath, "rb") as pickle_file:
                    map_set = pickle.load(pickle_file)
            except UnicodeDecodeError:
                with open(filepath, "rb") as pickle_file:
                    map_set = pickle.load(pickle_file, encoding="latin1")
        elif filepath.endswith(".json"):
            map_set = json.loads(open(filepath, "r").read())
        else:
            raise Exception("Invalid filteype", filepath)
        return map_set

    def map_regex(self, id, text, pattern_index=-1, pre_process=r"[^a-zA-Z0-9]"):
        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(self.patterns))
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        regex = self.patterns[pattern_index]["data"]
        if regex != re.compile(""):
            matches = regex.finditer(text)
            for m in matches:
                coord_map.add_extend(id, m.start(), m.start() + len(m.group()))
            self.patterns[pattern_index]["coordinate_map"] = coord_map
        elif regex == re.compile(""):
            matchall_list = re.split(r"(\s+)", text)
            matchall_list_cleaned = []
            for item in matchall_list:
                if len(item) > 0:
                    if item.isspace() == False:
                        split_item = re.split(r"(\s+)", re.sub(pre_process, " ", item))
                        for elem in split_item:
                            if len(elem) > 0:
                                matchall_list_cleaned.append(elem)
                    else:
                        matchall_list_cleaned.append(item)
            start_coordinate = 0
            for word in matchall_list_cleaned:
                start = start_coordinate
                stop = start_coordinate + len(word)
                word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
                if len(word_clean) == 0:
                    start_coordinate += len(word)
                    continue
                if regex.match(word_clean):
                    coord_map.add_extend(id, start, stop)
                start_coordinate += len(word)
            self.patterns[pattern_index]["coordinate_map"] = coord_map

    def map_regex_context(self, id="", text="", pattern_index=-1, pre_process=r"[^a-zA-Z0-9]"):
        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")
        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(self.patterns))
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        regex = self.patterns[pattern_index]["data"]
        context = self.patterns[pattern_index]["context"]
        try:
            context_filter = self.patterns[pattern_index]["context_filter"]
        except KeyError:
            warnings.warn(
                "deprecated missing context_filter field in filter "
                + str(pattern_index)
                + " of type regex_context, assuming 'all'",
                DeprecationWarning,
            )
            context_filter = "all"
        if context_filter == "all":
            current_include_map = self.include_map
            full_exclude_map = current_include_map.get_complement(id, text)
        else:
            context_filter_pattern_index = self.pattern_indexes[context_filter]
            full_exclude_map_coordinates = self.patterns[context_filter_pattern_index]["coordinate_map"]
            full_exclude_map = {}
            for start, stop in full_exclude_map_coordinates.filecoords(id):
                full_exclude_map[start] = stop
        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")
        matches = regex.finditer(text)
        for m in matches:
            phi_left = False
            phi_right = False
            match_start = m.span()[0]
            match_end = m.span()[1]
            phi_starts = []
            phi_ends = []
            for start in full_exclude_map:
                phi_starts.append(start)
                phi_ends.append(full_exclude_map[start])
            if match_start in phi_ends:
                phi_left = True
            if match_end in phi_starts:
                phi_right = True
            tokenized_matches = []
            match_text = m.group()
            split_match = re.split(r"(\s+)", re.sub(pre_process, " ", match_text))
            coord_tracker = 0
            for element in split_match:
                if element != "":
                    if not punctuation_matcher.match(element[0]):
                        current_start = match_start + coord_tracker
                        current_end = current_start + len(element)
                        tokenized_matches.append((current_start, current_end))
                        coord_tracker += len(element)
                    else:
                        coord_tracker += len(element)
            if (
                (context == "left" and phi_left == True)
                or (context == "right" and phi_right == True)
                or (context == "left_or_right" and (phi_right == True or phi_left == True))
                or (context == "left_and_right" and (phi_right == True and phi_left == True))
            ):
                for item in tokenized_matches:
                    coord_map.add_extend(id, item[0], item[1])
        self.patterns[pattern_index]["coordinate_map"] = coord_map

    def map_set(self, id, text, pattern_index=-1):
        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(self.patterns))
        map_set = self.patterns[pattern_index]["data"]
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        check_pos = False
        pos_set = set([])
        if "pos" in self.patterns[pattern_index]:
            pos_set = set(self.patterns[pattern_index]["pos"])
        if len(pos_set) > 0:
            check_pos = True
        cleaned = self.get_clean(id, text)
        pos_list = nltk.pos_tag(cleaned)
        start_coordinate = 0
        for tup in pos_list:
            word = tup[0]
            pos = tup[1]
            start = start_coordinate
            stop = start_coordinate + len(word)
            word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
            if len(word_clean) == 0:
                start_coordinate += len(word)
                continue
            if check_pos == False or (check_pos == True and pos in pos_set):
                if word_clean in map_set or word in map_set:
                    coord_map.add_extend(id, start, stop)
                else:
                    pass
            start_coordinate += len(word)
        self.patterns[pattern_index]["coordinate_map"] = coord_map

    def map_pos(self, id, text, pattern_index=-1):
        if pattern_index < 0 or pattern_index >= len(self.patterns):
            raise Exception("Invalid pattern index: ", pattern_index, "pattern length", len(self.patterns))
        if "pos" not in self.patterns[pattern_index]:
            raise Exception(
                "Mapping POS must include parts of speech", pattern_index, "pattern length", len(self.patterns)
            )
        coord_map = self.patterns[pattern_index]["coordinate_map"]
        pos_set = set(self.patterns[pattern_index]["pos"])
        cleaned = self.get_clean(id, text)
        pos_list = self.get_pos(id, cleaned)
        start_coordinate = 0
        for tup in pos_list:
            word = tup[0]
            pos = tup[1]
            start = start_coordinate
            stop = start_coordinate + len(word)
            word_clean = re.sub(r"[^a-zA-Z0-9]+", "", word.lower().strip())
            if len(word_clean) == 0:
                start_coordinate += len(word)
                continue
            if pos in pos_set:
                coord_map.add_extend(id, start, stop)
            start_coordinate += len(word)
        self.patterns[pattern_index]["coordinate_map"] = coord_map

    def get_exclude_include_maps(self, id, pattern, txt):
        coord_map = pattern["coordinate_map"]
        exclude = pattern["exclude"]
        try:
            filter_path = pattern["filepath"]
        except KeyError:
            filter_path = pattern["title"]
        if "phi_type" in pattern:
            phi_type = pattern["phi_type"]
        else:
            phi_type = "OTHER"
        for start, stop in coord_map.filecoords(id):
            if pattern["type"] != "regex_context":
                if exclude:
                    if not self.include_map.does_overlap(id, start, stop):
                        self.exclude_map.add_extend(id, start, stop)
                        self.phi_type_dict[phi_type][0].add_extend(id, start, stop)
                else:
                    if not self.exclude_map.does_overlap(id, start, stop):
                        self.include_map.add_extend(id, start, stop)
                        self.data_all_files[id]["non-phi"].append({
                            "start": start,
                            "stop": stop,
                            "word": txt[start:stop],
                            "filepath": filter_path,
                        })
                    else:
                        pass
            else:
                if exclude:
                    self.exclude_map.add_extend(id, start, stop)
                    self.include_map.remove(id, start, stop)
                    self.phi_type_dict[phi_type][0].add_extend(id, start, stop)
                else:
                    self.include_map.add_extend(id, start, stop)
                    self.exclude_map.remove(id, start, stop)
                    self.data_all_files[id]["non-phi"].append({
                        "start": start,
                        "stop": stop,
                        "word": txt[start:stop],
                        "filepath": filter_path,
                    })

    def deidentify(self, text):
        id = hashlib.md5(text.encode()).hexdigest()
        for i, pat in enumerate(self.patterns):
            self.patterns[i]["coordinate_map"] = CoordinateMap()
        self.data_all_files[id] = {"text": text, "phi": [], "non-phi": []}
        self.exclude_map.add_file(id)
        self.include_map.add_file(id)
        for phi_type in self.phi_type_list:
            self.phi_type_dict[phi_type][0].add_file(id)
        for i, pat in enumerate(self.patterns):
            if pat["type"] == "regex":
                self.map_regex(id=id, text=text, pattern_index=i)
            elif pat["type"] == "set":
                self.map_set(id=id, text=text, pattern_index=i)
            elif pat["type"] == "regex_context":
                self.map_regex_context(id=id, text=text, pattern_index=i)
            elif pat["type"] == "pos_matcher":
                self.map_pos(id=id, text=text, pattern_index=i)
            else:
                raise Exception("Error, pattern type not supported: ", pat["type"])
            self.get_exclude_include_maps(id, pat, text)
        self.full_exclude_map[id] = self.include_map.get_complement(id, text)
        for phi_type in self.phi_type_list:
            for start, stop in self.phi_type_dict[phi_type][0].filecoords(id):
                self.data_all_files[id]["phi"].append({
                    "start": start,
                    "stop": stop,
                    "word": text[start:stop],
                    "phi_type": phi_type,
                    "filepath": "",
                })
        tagdata = self.data_all_files[id]
        return tagdata["phi"]
