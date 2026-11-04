ANSI_ELEMENTS = [
    "[\\u001B\\u009B][[\\]()#;?]*(?:(?:(?:[a-zA-Z\\d]*(?:;[-a-zA-Z\\d\\/#&.:=?%@~_]*)*)?\\u0007)",
    "(?:(?:\\d{1,4}(?:;\\d{0,4})*)?[\\dA-PR-TZcf-ntqry=><~]))",
]

ASTRAL_ELEMENTS = ["[\ud800-\udbff][\udc00-\udfff]"]

CHINESE_ELEMENTS = ["[\u4e00-\u9fa5]", "[\uff00-\uffff]"]
