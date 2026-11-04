import numpy
import itertools
import re


class CoordinateMap:
    def __init__(self, pattern={"title": "untitled"}, debug=False):
        self.map = {}
        self.coord2pattern = {}
        self.pattern = pattern
        self.debug = debug
        self.all_coords = {}

    def add(self, id, start, stop, overlap=False, pattern=""):
        if id not in self.map:
            self.map[id] = {}
        if id not in self.all_coords:
            self.all_coords[id] = {}
        if not overlap:
            if self.does_overlap(id, start, stop):
                return False, "Error, overlaps were found: {} {} {}".format(id, start, stop)
        self.map[id][start] = stop
        for i in range(start, stop):
            self.all_coords[id][i] = 1
        if pattern != "":
            self.add_pattern(id, start, stop, pattern)
        return True, None

    def add_pattern(self, id, start, stop, pattern):
        if id not in self.coord2pattern:
            self.coord2pattern[id] = {}
        if start not in self.coord2pattern[id]:
            self.coord2pattern[id][start] = []
        self.coord2pattern[id][start].append(pattern)

    def add_extend(self, id, start, stop, pattern=""):
        if self.debug:
            print("add_extend", start, stop)
        if id not in self.map:
            self.map[id] = {}
        overlaps = self.max_overlap(id, start, stop)

        def clear_overlaps(id, lst):
            for o in lst:
                self.remove(id, o["orig_start"], o["orig_end"])

        if len(overlaps) == 0:
            self.add(id, start, stop, pattern=pattern, overlap=True)
        elif len(overlaps) == 1:
            clear_overlaps(id, overlaps)
            o = overlaps[0]
            self.add(id, o["new_start"], o["new_stop"], pattern=pattern, overlap=True)
        else:
            clear_overlaps(id, overlaps)
            o1 = overlaps[0]
            o2 = overlaps[-1]
            self.add(id, o2["new_start"], o1["new_stop"], pattern=pattern, overlap=True)
        return True, None

    def remove(self, filename, start, stop):
        if filename not in self.map:
            raise Exception("Filename does not exist", filename)
        if start in self.map[filename]:
            del self.map[filename][start]
        for i in range(start, stop + 1):
            if i in self.all_coords:
                del self.all_coords[i]
        return True, None

    def scan(self):
        for fn in self.map:
            coords = list(self.map[fn].keys())
            coords.sort()
            for coord in coords:
                yield fn, coord, self.map[fn][coord]

    def keys(self):
        for fn in self.map:
            yield fn

    def get_coords(self, id, start):
        stop = self.map[id][start]
        return start, stop

    def filecoords(self, id):
        if id not in self.map:
            return
        coords = sorted(self.map[id].keys())
        for coord in coords:
            yield coord, self.map[id][coord]

    def does_exist(self, id, index):
        if index in self.map[id]:
            return True
        return False

    def does_overlap(self, id, start, stop):
        ranges = [list(range(key, self.map[id][key] + 1)) for key in self.map[id]]
        all_coords = [item for sublist in ranges for item in sublist]
        for i in range(start, stop + 1):
            if i in all_coords:
                return True
        return False

    def calc_overlap(self, id, start, stop):
        overlaps = []
        for s in self.map[id]:
            e = self.map[id][s]
            if s >= start or s <= stop:
                if e <= stop:
                    overlaps.append({"start": s, "stop": e})
                else:
                    overlaps.append({"start": s, "stop": stop})
            elif e >= start or e <= stop:
                if s >= start:
                    overlaps.append({"start": s, "stop": e})
                else:
                    overlaps.append({"start": start, "stop": e})
        return overlaps

    def max_overlap(self, id, start, stop):
        overlaps = []
        for s in self.map[id]:
            e = self.map[id][s]
            if start >= s and start <= e:
                if stop >= e:
                    overlaps.append({"orig_start": s, "orig_end": e, "new_start": s, "new_stop": stop})
                else:
                    overlaps.append({"orig_start": s, "orig_end": e, "new_start": s, "new_stop": e})
            elif stop >= s and stop <= e:
                if start <= s:
                    overlaps.append({"orig_start": s, "orig_end": e, "new_start": start, "new_stop": e})
                else:
                    overlaps.append({"orig_start": s, "orig_end": e, "new_start": s, "new_stop": e})
        return overlaps

    def add_file(self, id):
        self.map[id] = {}

    def get_complement(self, filename, text):
        complement_coordinate_map = {}
        current_map_coordinates = []
        for start_key in self.map[filename]:
            start = start_key
            stop = self.map[filename][start_key]
            current_map_coordinates += range(start, stop)
        text_coordinates = list(range(0, len(text)))
        complement_coordinates = list(set(text_coordinates) - set(current_map_coordinates))
        punctuation_matcher = re.compile(r"[^a-zA-Z0-9*]")
        for i in range(0, len(text)):
            if punctuation_matcher.match(text[i]):
                if i in complement_coordinates:
                    complement_coordinates.remove(i)

        def to_ranges(iterable):
            iterable = sorted(set(iterable))
            for key, group in itertools.groupby(enumerate(iterable), lambda t: t[1] - t[0]):
                group = list(group)
                yield group[0][1], group[-1][1] + 1

        complement_coordinate_ranges = list(to_ranges(complement_coordinates))
        for tup in complement_coordinate_ranges:
            start = tup[0]
            stop = tup[1]
            complement_coordinate_map[start] = stop
        return complement_coordinate_map
