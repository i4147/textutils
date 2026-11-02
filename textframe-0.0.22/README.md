```python
def table_string(table_columns: List[dict], table_dict: List[dict], header: bool = True, footer: bool = True) -> str:

    # analyse table_dict for lengths?
    table_width = 1
    return_string = ""
    for table_column in table_columns:
        table_width += table_column["width"] + 1

    if header:
        # return_string += f"{'=' * table_width}\n"
        for i, table_column in enumerate(table_columns):
            if i == 0:
                return_string += (
                    f"  {table_column['name']}{' ' * (table_column['width'] - len(table_column['name']) - 1)}"
                )
        return_string += "|\n"
        for table_column in table_columns:
            return_string += f"┼{'-' * table_column['width']}"
        return_string += "|\n"
        for table_column in table_columns:
            return_string += f"|{' ' * table_column['width']}"
        return_string += "|\n"
        for table_column in table_columns:
            return_string += f"|{' ' * table_column['width']}"
        return_string += "|\n"
        for table_column in table_columns:
            return_string += f"|{' ' * table_column['width']}"
        return_string += "|\n"

    # return_string += f"{'=' * table_width}\n"

    for table_row in table_dict:
        for table_cell in table_row.items():
            pass

    return return_string


test_columns = [
    {"width": 40, "name": "Projects"},
    {"width": 20, "name": "Epochs"},
    {"width": 20, "name": "Collections"},
]

print(table_string(test_columns, test_columns))

"""

┏━━━━━━━━┳━━━━━━━┓
┃ item   ┃   qty ┃
┣━━━━━━━━╋━━━━━━━┫
┃ spam   ┃    42 ┃
┣━━━━━━━━╋━━━━━━━┫
┃ eggs   ┃   451 ┃
┣━━━━━━━━╋━━━━━━━┫
┃ bacon  ┃     0 ┃
┗━━━━━━━━┻━━━━━━━┛

╔════════════════╗
║ item   ┃   qty ║
╠════════════════╣
║ spam   ┃    42 ║
║━━━━━━━━╋━━━━━━━║
║ eggs   ┃   451 ║
║━━━━━━━━╋━━━━━━━║
║ bacon  ┃     0 ║
╚════════════════╝

╔════════════════╗
║ item   ┃   qty ║
╠════════════════╣
║ spam   ┃    42 ║
╠════════════════╣
║ eggs   ┃   451 ║
╠════════════════╣
║ bacon  ┃     0 ║
╚════════════════╝

┏━━━━━━━━┯━━━━━━━┓
┃ item   │   qty ┃
┠────────┼───────┨
┃ spam   │    42 ┃
┠────────┼───────┨
┃ eggs   │   451 ┃
┠────────┼───────┨
┃ bacon  │     0 ┃
┗━━━━━━━━┷━━━━━━━┛

┏━━━━━━━━┳━━━━━━━┓
┃ item   ┃   qty ┃
┣━━━━━━━━╇━━━━━━━┫
┃ spam   │    42 ┃
┠────────┼───────┨
┃ eggs   │   451 ┃
┠────────┼───────┨
┃ bacon  │     0 ┃
┗━━━━━━━━┷━━━━━━━┛


    ╔════════════════════════════════════════════╤═════╤═════╤═════╤═════╗
    ║ asdasdasd                        asdasdasd │ asd │ asd │ asd │ sdf ║
    ╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
    ║ asd                                        │ asd │ asd │ asd │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝


╔════════════════════════════════════════════════════════════════════╗
║ PROJECT: Some Project                                              ║
╟────────────────────────────────────────────────────────────────────╢
║ And here is the project descript, whatever it might be. It might   ║
║ even be several lines.                                             ║
╠════════════════════════════════════════════╤═════╤═════╤═════╤═════╣
║ EPOCHS                                     │ asd │ asd │ asd │ sdf ║
╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
║ asd                                        │ asd │ asd │ asd │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝


╔════════════════════════════════════════════════════════════════════╗
║ PROJECT: Some Project                                              ║
╟────────────────────────────────────────────────────────────────────╢
║ And here is the project descript, whatever it might be. It might   ║
║ even be several lines.                                             ║
╠════════════════════════════════════════════╤═════╤═════╤═════╤═════╣
║                   EPOCHS                   │ asd │ asd │ asd │ sdf ║
╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
║ asd                                        │ asd │ asd │ asd │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝




╔════════════════════════════════════════════════════════════════════╗
║ PROJECT: Some Project                                              ║
╟────────────────────────────────────────────────────────────────────╢
║ And here is the project descript, whatever it might be.            ║
╠════════════════════════════════════════════╤═════╤═════╤═════╤═════╣
║ EPOCHS                                     │ asd │ asd │ asd │ sdf ║
╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
║ Getting started                            │ asd │ asd │ asd │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ Moving forward                             │ sdf │ sdf │ sdf │ sdf ║
╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
║ Cleaning up                                │ sdf │ sdf │ sdf │ sdf ║
╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝




















╔════════════════════════════════════════════╤═══════╤═══════╤═══════╤════════╗
║ asdasdasd                                  │ asd   │ asd   │ asd   │ asd    ║
╟────────────────────────────────────────────┼───────┼───────┼───────┼────────╢
║ asd                                        │ asd   │ asd   │ asd   │ asd    ║
║ sdf                                        │ asd   │ asd   │ asd   │ asd    ║
║ sdf                                        │ asd   │ asd   │ asd   │ asd    ║
╚════════════════════════════════════════════╧═══════╧═══════╧═══════╧════════╝


┌────────────────────────────────────────────┬─────┬─────┬─────┬─────┐
│ asdasdasd                                  │ asd │ asd │ asd │ sdf │
├────────────────────────────────────────────┼─────┼─────┼─────┼─────┤
│ asd                                        │ asd │ asd │ asd │ sdf │
│ sdf                                        │ sdf │ sdf │ sdf │ sdf │
│ sdf                                        │ sdf │ sdf │ sdf │ sdf │
└────────────────────────────────────────────┴─────┴─────┴─────┴─────┘




┌────────────────────────────────────────────┬─────┬─────┬─────┬─────┐
│ asdasdasd                        asdasdasd │ asd │ asd │ asd │ sdf │
╞════════════════════════════════════════════╪═════╪═════╪═════╪═════╡
│ asd                                        │ asd │ asd │ asd │ sdf │
│ sdf                                        │ sdf │ sdf │ sdf │ sdf │
│ sdf                                        │ sdf │ sdf │ sdf │ sdf │
└────────────────────────────────────────────┴─────┴─────┴─────┴─────┘














    ╔════════════════════════════════════════════╤═══════════════════════╗
    ║                                            │     SUPER HEADER      ║
    ║ CLIENTS                                    │ ABC │ ABC │ ABC │ ABC ║
    ╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
    ║ asd                                        │ asd │ asd │ asd │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝


    ╔════════════════════════════════════════════╤═══════════════════════╗
    ║                                            │                       ║
    ║                                            │     super header      ║
    ║                                            │                       ║
    ║ asdasdasd                                  │ asd │ asd │ asd │ sdf ║
    ╠════════════════════════════════════════════╪═════╪═════╪═════╪═════╣
    ║ asd                                        │ asd │ asd │ asd │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╟────────────────────────────────────────────┼─────┼─────┼─────┼─────╢
    ║ sdf                                        │ sdf │ sdf │ sdf │ sdf ║
    ╚════════════════════════════════════════════╧═════╧═════╧═════╧═════╝

























"""


"""
│ ┃ ║

─ ━ ═

┌ ┏ ╔ ┍ ┎ ╒ ╓ * 4

├ ┣ ╠ ┠ ┝ ╟ ╞

┤ ┫ ╣ ┨ ┥ ╢ ╡

┼ ╋ ╬ ╂ ┿ ╀ ╁ ╇ ╈ ╫ ╪ 
"""

x = ["thin", "thick", "thin┿"]

"""
│ ║

─ ═

┌ ╔ ╒ ╓ * 4

├ ╠ ╟ ╞

┤ ╣ ╢ ╡

┼ ╬ ╫ ╪ 
"""

"""
only thin for inner column... yes!

│ ┃ ║

─ ━ ═

┌ ┏ ╔ ┍ ┎ ╒ ╓     * 4

├ ┣ ╠ ┠ ┝ ╟ ╞ ║ ┃

┤ ┫ ╣ ┨ ┥ ╢ ╡ ║

┼ ┿ ╪ 
"""

"""
only thin for inner column... 
same same outer border...
yes yes!!!

│ ┃ ║

─ ━ ═

┌ ┏ ╔     * 4

├ ┣ ╠ ┠ ┝ ╟ ╞ ║ ┃

┤ ┫ ╣ ┨ ┥ ╢ ╡ ║ ┃

┼ ┿ ╪ 
"""


"""
only thin for inner column... 
same same outer border...
yes yes!!!

(sorted by outer first)

│ ┃ ║

─ ━ ═

┌ ┏ ╔     * 4

├ ┝ ╞ ┠ ┠ ┃ ╟ ║ ╠

┤ ┥ ╡ ┨ ┫ ┃ ╢ ║ ╣

┼ ┿ ╪ 

manageable...
"""

left_side_matrix = {
    "thin": {"thin": "├", "thick": "┝", "double": "╞"},
    "thick": {"thin": "┠", "thick": "┣", "double": "┃"},
    "double": {"thin": "╟", "thick": "║", "double": "╠"},
}

right_side_matrix = {
    "thin": {"thin": "┤", "thick": "┥", "double": "╡"},
    "thick": {"thin": "┨", "thick": "┫", "double": "┃"},
    "double": {"thin": "╢", "thick": "║", "double": "╣"},
}
```

```python
# A - is this an outer_border
# 1 - determine border type
# 2 - populate edge characters (in array [a])
# 2 - populate line (in array [b]) with line type
# 3 - calculate intersections (in an array of arrays [c])
# 5 - populate intersection (in array [b])
# 6 - generate string
# B - is this a line row (should really only be between frames, me thinks...) (maybe each table row is a frame?)
# 1 - determine line type
# 2 - populate edge characters (in array [a])
# 3 - populate line (in array [b]) with line type
# 4 - calculate intersections (in an array of arrays [c])
# 5 - populate intersection (in array [b])
# 6 - generate string
# C - is this a text line
# 1 - populate edge characters (in array [a])
# 2 - generate string


# how much of this should be done above? ie: should the print just have complete frames? just handling the edge character?
# (more specifically, handling the line rows above?)

row_index = 0
```

### thought for the future:

the reason for having each frame fully stringify itself and have `to_string` only handle the lines between frames was an attempt to balance to three considerations:

- the dividing line can only be drawn when the frames both above and below are known ( so in `to_string` )
- the original idea to leave padding and outer borders to `to_string` and the rest in the ... would be complicated because of the table row lines interacting with outer borders
- reducing load on the `to_string` method to ensure smooth printing (perhaps not necessary... perform time tests)

maybe in the future it would be better to treat each row of the table as a frame and have `to_string` stringify everything

probably this will be less confusing and better unify concerns

`new_to_string` & `new_add_` methods... to perform A/B tests

performance vs clean code...

(thought: perhaps the end of each `add_` function could render all above??? could get messy...)

maybe perform speed test in constrained VM/container

finish everything else before doing this... (so not having to go too far back in time in case want to undo later...)

NOTE: currently... the table row lines are generated only once and reused...

one solution would be to define the line types... whether divider or text (so border can be correctly rendered) => too many checks (specific only for table...) in `to_string`

the trick is that there is so much logic specific to tables... => blank dividers for instance (actually this would not be a problem since this doesn't affect the row divider)

current timings:
- `add_table` = 0.119ms
- `to_string` = 0.047ms
- `print` = 0.014ms
- `row_frame_divider` = 0.006ms
---
- for 20 row table, `row_frame_divider` would cost 0.12ms (vs 0.006 currently)
- for 100 row table, `row_frame_divider` would cost 0.6ms (vs 0.006 currently)
---

conclusion: leave as is until a best of both worlds (clean and performant) solution can be found... the performance differences are too great.

---

