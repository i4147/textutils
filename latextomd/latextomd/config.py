DEFAULT_OPTIONS = {"remove_comments": True, "strip_lines": True}

replace_simple = [
    ["\\ds\\", "\\displaystyle\\"],
    ["$\\C$", "\\mathcal{C}"],
    ["\\e^", "\\text{e}^"],
    ["\\mathscr", "\\mathcal"],
    ["\\[", "$$"],
    ["\\]", "$$"],
    ["\n$$", "\n$$\n"],
    ["$$\n", "\n$$\n"],
    ["\\begin", "\n\\begin"],
    ["\\begin{center}", ""],
    ["\\end{center}", ""],
    ["\\begin{solution}", ":::startsolution\n"],
    ["\\end{solution}", "\n\n:::endsolution"],
]


del_commands = [
    "vspace",
    "Bareme",
    "cornouaille",
    "renewcommand",
    "setbar",
    "esp",
    "encadre",
    "ref",
    "arraycolsep",
    "label",
    "renewcommand",
    "hspace",
    "parindent",
    "raisebox",
    "rhead",
    "lhead",
    "lfoot",
    "rfoot",
    "addtolength",
    "pagestyle",
    "thispagestyle",
    "marginpar",
    "newpage",
    "hfill",
    "medskip",
    "bigskip",
    "smallskip",
    "setlength",
    "decofourleft",
    "footrulewidth",
    "decofourright",
]

del_environnements = [r"\begin{center}", r"\end{center}"]

del_blocks = ["center"]

replace_commands = [
    ["chapter", "# S_T_R"],
    ["section", "## S_T_R"],
    ["subsection", "### S_T_R"],
    ["textbf", "**S_T_R**"],
    ["textsc", "S_T_R"],
    ["emph", "_S_T_R_"],
]
blocks = [
    [r"\\begin\{multicols\}\{((?P<arg>.*?))\}", ""],
    [r"\\end{multicols}", ""],
    [
        r"\\begin\{definition\}(\[(?P<block_title>.*?)\])?",
        r"\n:::definition Définition: \2\n\n",
    ],
    [r"\\end{definition}", "\n\n:::"],
]
math_sub = [
    [r"\\np\{((?P<arg>.*?))\}", r"\1"],
    [r"\\nombre\{((?P<arg>.*?))\}", r"\1"],
    [r"\\textsf\{((?P<arg>.*?))\}", r"\1"],
    [r"\\Large(\{(?P<arg>.*?)\})?", r"\1"],
    [r"\\parbox\{((?P<arg>.*?))\}", ""],
    [r"\\end\{((?P<arg>.*?))\}", r"\\end{\1}\n"],
    [r"\\Oijk", r"$\\left(\\text{O};~\\vect{i},~\\vect{j},~\\vect{k}\\right)$"],
    [r"\\Ouv", r"$\\left(\\text{O};~\\vect{u},~\\vect{v}\\right)$"],
    [r"\\Oij", r"$\\left(\\text{O};~\\vect{i},~\\vect{j}\\right)$"],
    [r"\\vect\{((?P<arg>.*?))\}", r"\\overrightarrow{\1}"],
    [r"\\e(\W)", r"\1"],
] + blocks


postpandoc = [
    [r"\\textsf\{((?P<arg>.*?))\}", r"\1"],
    [r"\\Large(\{(?P<arg>.*?)\})?", r"\1"],
    [r"\\parbox\{((?P<arg>.*?))\}", ""],
    [r"\\end\{((?P<arg>.*?))\}", r"\\end{\1}\n"],
    [r"\\Oijk", r"$\\left(\\text{O};~\\vect{i},~\\vect{j},~\\vect{k}\\right)$"],
    [r"\\Ouv", r"$\\left(\\text{O};~\\vect{u},~\\vect{v}\\right)$"],
    [r"\\Oij", r"$\\left(\\text{O};~\\vect{i},~\\vect{j}\\right)$"],
    [r"\\vect\{((?P<arg>.*?))\}", r"\\overrightarrow{\1}"],
    [r"\\rbrace", r"\\}"],
    [r"\\strut", ""],
    [r"\\e(\W)", r"\1"],
]
