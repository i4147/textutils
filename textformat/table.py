class TableFormatter:
    @staticmethod
    def generate(headers, data):
        col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *data)]

        def build_border():
            return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        def format_row(row):
            return "| " + " | ".join(f"{str(item).ljust(w)}" for item, w in zip(row, col_widths)) + " |"

        border = build_border()
        rows = [format_row(headers), border] + [format_row(row) for row in data]
        return f"{border}\n" + "\n".join(rows) + f"\n{border}"
