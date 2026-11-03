def isfloat(value):
    try:
        float(value)
        return True
    except:
        return False


def isint(value):
    try:
        int(value)
        return True
    except:
        return False


CONVERTERS = {"IntType": int, "FloatType": float, "StringType": lambda x: x}


def pick_type(types):
    type_set = set(types)
    if len(type_set) == 1:
        return list(type_set)[0]
    elif {"IntType", "FloatType"} == type_set:
        return "FloatType"
    else:
        return "StringType"


def get_column_types(content):
    test_count = min(len(content), 5)
    col_count = len(content[0])
    all_types = [[] for i in range(col_count)]
    for r_ind in range(test_count):
        for col_ind, col in enumerate(content[r_ind]):
            if isint(col):
                all_types[col_ind].append("IntType")
            elif isfloat(col):
                all_types[col_ind].append("FloatType")
            else:
                all_types[col_ind].append("StringType")
    column_types = [pick_type(types) for types in all_types]
    return column_types


def coerce_types(content):
    if len(content) == 0:
        return content
    column_types = get_column_types(content)
    coerced_content = []
    for row in content:
        c_row = []
        for col_ind, col in enumerate(row):
            try:
                col = CONVERTERS[column_types[col_ind]](col)
            except ValueError:
                col = col
            c_row.append(col)
        coerced_content.append(c_row)
    return coerced_content
