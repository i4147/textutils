# textstyle

> Simple, powerful, cross-platform terminal text styling for Python

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Cross Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/crystallinecore/textstyle)

**textstyle** is a lightweight Python library that makes terminal text styling effortless. With support for colors, backgrounds, text styles, and an intuitive markup format, you can create beautiful CLI applications with just a few lines of code.

---

## ✨ Features

- **Rich Color Support** - Named colors, hex codes (#FF5733), and RGB tuples
-  **Text Styling** - Bold, italic, underline, strikethrough, and more
-  **Markup Format** - Intuitive XML-style tags for easy formatting
-  **Theme System** - Built-in themes (dark/light) and custom themes
-  **Utility Functions** - Strip tags, clean ANSI codes, measure visible length
-  **Cross-Platform** - Works seamlessly on Linux, macOS, and Windows
-  **NO_COLOR Support** - Respects NO_COLOR and FORCE_COLOR environment variables
-  **Zero Dependencies** - Pure Python, no external packages required
-  **Composable** - Mix and match styles, nest tags, create reusable components

---

## 📦 Installation

```bash
pip install textstyle
```

Or install from source:

```bash
git clone https://github.com/crystallinecore/textstyle.git
cd textstyle
pip install -e .
```

---

## 🚀 Quick Start

```python
import textstyle as ts

# Basic styling
print(ts.style("Error", color="red", look="bold"))
print(ts.style("Success", color="green", look="bold"))

# Markup format
print(ts.format("This is <red>red</red> and <bold>bold</bold>!"))

# Hex colors
print(ts.style("Custom", color="#FF5733", look="bold"))

# Create custom styles
ts.create("error", color="red", look="bold")
print(ts.format("An <error>error</error> occurred!"))

# Use themes
ts.set_theme("dark")
print(ts.format("<error>Error:</error> Connection failed"))
```

## 📖 Documentation

### Basic Usage

#### `style(text, color=None, bg=None, look=None)`

Apply styling to text directly.

```python
import textstyle as ts

# Simple colors
print(ts.style("Hello", color="red"))
print(ts.style("World", color="blue", look="bold"))

# Background colors
print(ts.style("Alert", color="white", bg="red", look="bold"))

# Hex colors
print(ts.style("Brand", color="#FF5733"))

# RGB tuples
print(ts.style("Custom", color=(255, 87, 51)))

# Multiple looks
print(ts.style("Fancy", color="cyan", look=["bold", "underline"]))
```

**Available colors:**
- `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- `bright_black`, `bright_red`, `bright_green`, `bright_yellow`, `bright_blue`, `bright_magenta`, `bright_cyan`, `bright_white`

**Available looks:**
- `bold`, `dim`, `italic`, `underline`, `blink`, `reverse`, `hidden`, `strikethrough`

**Background colors:**
- Prefix any color name with `bg_` (e.g., `bg="red"` or `bg="bright_blue"`)

---

#### `format(text)`

Format text using markup-style tags.

```python
import textstyle as ts

# Predefined color tags
print(ts.format("This is <red>red</red> text"))

# Predefined look tags
print(ts.format("This is <bold>bold</bold> text"))

# Background tags
print(ts.format("Alert: <bg_red><white>WARNING</white></bg_red>"))

# Hex color tags
print(ts.format("Brand: <#FF5733>orange</#FF5733>"))

# Nested tags
print(ts.format("<red><bold>Bold Red</bold></red>"))

# Complex combinations
print(ts.format("Status: <green>Connected</green> | Warnings: <yellow>2</yellow> | Errors: <red>0</red>"))
```

---

### Custom Styles

#### `create(name, color=None, bg=None, look=None)`

Create reusable custom styles.

```python
import textstyle as ts

# Create custom styles
ts.create("error", color="red", look="bold")
ts.create("success", color="green", look="bold")
ts.create("warning", color="yellow", look="bold")
ts.create("highlight", color="black", bg="yellow")

# Use in format()
print(ts.format("<error>ERROR:</error> Connection failed"))
print(ts.format("<success>SUCCESS:</success> File saved"))
print(ts.format("Please <highlight>note</highlight> this"))

# Use as function (dynamic attribute access)
print(ts.error("Direct error styling"))
print(ts.success("Direct success styling"))
```

#### `delete(name)`

Remove a custom style.

```python
ts.delete("error")  # Returns True if deleted, False if not found
```

---

### Theme System

#### `set_theme(theme)`

Apply a theme with multiple predefined styles.

**Built-in themes:**

```python
import textstyle as ts

# Dark theme (bright colors)
ts.set_theme("dark")
print(ts.format("<error>Error</error> <success>Success</success>"))

# Light theme (standard colors)
ts.set_theme("light")
print(ts.format("<warning>Warning</warning> <info>Info</info>"))
```

**Custom themes:**

```python
ts.set_theme({
    "primary": {"color": "#007AFF", "look": "bold"},
    "secondary": {"color": "#5856D6"},
    "danger": {"color": "white", "bg": "#FF3B30", "look": "bold"},
    "success": {"color": "#34C759", "look": "bold"},
    "muted": {"color": "bright_black"},
})

print(ts.format("<primary>Primary Button</primary>"))
print(ts.format("<danger>Delete Account</danger>"))
```

**Built-in theme styles:**
- `error` - Error messages
- `success` - Success messages
- `warning` - Warning messages
- `info` - Informational messages
- `debug` - Debug output
- `critical` - Critical alerts

---

### Temporary Styles

#### `temporary(name, color=None, bg=None, look=None)`

Context manager for temporary styles.

```python
import textstyle as ts

# Temporary style exists only in context
with ts.temporary("temp", color="magenta", look="italic"):
    print(ts.format("<temp>This is temporary</temp>"))
    print(ts.format("Still using <temp>temp</temp>"))

# After context, style is automatically deleted
print(ts.format("<temp>This is plain text</temp>"))
```

---

### Utility Functions

#### `strip(text)`

Remove all markup tags from text.

```python
import textstyle as ts

markup = "<red>Hello</red> <bold>World</bold>"
print(ts.strip(markup))  # Output: "Hello World"
```

#### `clean(text)`

Remove all ANSI escape codes from text.

```python
import textstyle as ts

styled = ts.style("Hello", color="red", look="bold")
print(ts.clean(styled))  # Output: "Hello"
```

#### `length(text)`

Calculate visible text length (ignoring ANSI codes).

```python
import textstyle as ts

styled = ts.style("Hello", color="red", look="bold")
print(len(styled))  # Output: 19 (includes ANSI codes)
print(ts.length(styled))  # Output: 5 (visible length)
```

#### `enable()` / `disable()`

Globally enable or disable styling.

```python
import textstyle as ts

print(ts.style("Styled", color="red"))  # Colored output

ts.disable()
print(ts.style("Plain", color="red"))  # Plain text

ts.enable()
print(ts.style("Styled", color="red"))  # Colored output again
```

---

## 🎯 Real-World Examples

### Logging System

```python
import textstyle as ts
import time

ts.set_theme({
    "timestamp": {"color": "bright_black"},
    "info": {"color": "cyan"},
    "success": {"color": "green", "look": "bold"},
    "error": {"color": "red", "look": "bold"},
})


def log(level, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(ts.format(f"<timestamp>[{timestamp}]</timestamp> <{level}>{level.upper():<8}</{level}> {message}"))


log("info", "Application started")
log("success", "Database connected")
log("error", "Failed to load configuration")
```

### CLI Menu

```python
import textstyle as ts

ts.set_theme({
    "title": {"color": "cyan", "look": "bold"},
    "option": {"color": "green"},
    "key": {"color": "yellow", "look": "bold"},
})

menu = """
<title>╔═══════════════════════════╗</title>
<title>║     MAIN MENU             ║</title>
<title>╚═══════════════════════════╝</title>

<key>[1]</key> <option>New Project</option>
<key>[2]</key> <option>Open Project</option>
<key>[3]</key> <option>Settings</option>
<key>[Q]</key> <option>Quit</option>
"""

print(ts.format(menu))
```

### Progress Bar

```python
import textstyle as ts
import time

ts.set_theme({
    "filled": {"color": "green", "look": "bold"},
    "empty": {"color": "bright_black"},
    "percent": {"color": "cyan", "look": "bold"},
})


def progress(current, total):
    percent = int((current / total) * 100)
    filled = int((current / total) * 20)
    empty = 20 - filled

    bar = ts.format(f"<filled>{'█' * filled}</filled><empty>{'░' * empty}</empty>")

    print(f"\r{bar} {ts.format(f'<percent>{percent}%</percent>')}", end="", flush=True)


for i in range(101):
    progress(i, 100)
    time.sleep(0.05)
```

### Data Table

```python
import textstyle as ts

ts.set_theme({
    "header": {"color": "cyan", "look": "bold"},
    "good": {"color": "green"},
    "warn": {"color": "yellow"},
    "error": {"color": "red"},
})

print(
    ts.format("""
┌─────────────┬─────────┬──────┐
│ <header>Server</header>      │ <header>Status</header>  │ <header>CPU</header>  │
├─────────────┼─────────┼──────┤
│ web-01      │ <good>● Up</good>    │ 23%  │
│ web-02      │ <warn>◐ Warn</warn>  │ 78%  │
│ db-01       │ <error>○ Down</error>  │ 95%  │
└─────────────┴─────────┴──────┘
""")
)
```

### Form Validation

```python
import textstyle as ts

ts.set_theme({
    "field": {"color": "cyan", "look": "bold"},
    "valid": {"color": "green"},
    "invalid": {"color": "red"},
})

validation = """
<field>Email:</field> user@example.com <valid>✓ Valid</valid>
<field>Password:</field> ********** <valid>✓ Strong</valid>
<field>Username:</field> ab <invalid>✗ Too short</invalid>
<field>Phone:</field> 555-1234 <valid>✓ Valid</valid>
"""

print(ts.format(validation))
```

### Git-Style Output

```python
import textstyle as ts

ts.set_theme({
    "branch": {"color": "cyan", "look": "bold"},
    "added": {"color": "green"},
    "modified": {"color": "yellow"},
    "deleted": {"color": "red"},
})

output = """
On branch <branch>main</branch>

Changes to be committed:
  <added>new file:   src/app.py</added>
  <added>new file:   README.md</added>

Changes not staged:
  <modified>modified:   config.yaml</modified>
  <deleted>deleted:    old_file.py</deleted>
"""

print(ts.format(output))
```

---

## 🎨 Color Reference

### Named Colors

```python
# Standard colors
black, red, green, yellow, blue, magenta, cyan, white

# Bright colors
(
    bright_black,
    bright_red,
    bright_green,
    bright_yellow,
)
bright_blue, bright_magenta, bright_cyan, bright_white
```

### Hex Colors

```python
# Full hex
print(ts.style("Text", color="#FF5733"))

# Short hex
print(ts.style("Text", color="#F00"))

# In markup
print(ts.format("<#FF5733>Colored text</#FF5733>"))
```

### RGB Colors

```python
# RGB tuples
print(ts.style("Text", color=(255, 87, 51)))
print(ts.style("Text", bg=(0, 128, 255)))
```

---

## 🌍 Environment Variables

textstyle respects standard terminal environment variables:

### `NO_COLOR`

Disable all styling when set (any value):

```bash
export NO_COLOR=1
python your_script.py  # No colors or styles
```

### `FORCE_COLOR`

Force enable styling even in non-TTY environments:

```bash
export FORCE_COLOR=1
python your_script.py | tee output.log  # Colors preserved
```

---

## 🔧 Advanced Usage

### Nested Tags

```python
import textstyle as ts

print(ts.format("<red><bold>Error:</bold> <underline>Connection failed</underline></red>"))

print(ts.format("<bg_blue><white>Info: <bold>Processing...</bold></white></bg_blue>"))
```

### Combining Multiple Styles

```python
import textstyle as ts

# Multiple looks in style()
print(ts.style("Text", color="red", look=["bold", "underline"]))

# Combining custom styles
ts.create("alert", color="white", bg="red", look="bold")
ts.create("code", color="cyan", look="italic")

print(ts.format("<alert>Warning:</alert> Check <code>config.yaml</code>"))
```

### Dynamic Styling

```python
import textstyle as ts


def status_color(value):
    if value < 50:
        return "green"
    elif value < 80:
        return "yellow"
    else:
        return "red"


cpu_usage = 75
print(ts.style(f"CPU: {cpu_usage}%", color=status_color(cpu_usage), look="bold"))
```

### Working with Alignment

```python
import textstyle as ts


# Align with visible length
def align_text(text, width):
    visible_len = ts.length(text)
    padding = width - visible_len
    return text + " " * padding


styled = ts.style("Status", color="green", look="bold")
print(align_text(styled, 20) + "OK")
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python -m textstyle
```

Or create your own tests:

```python
import textstyle as ts

# Disable for testing
ts.disable()
assert ts.style("Test", color="red") == "Test"

# Re-enable
ts.enable()
assert "\033[" in ts.style("Test", color="red")
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue with details
2. **Suggest features** - Describe your use case
3. **Submit PRs** - Fork, create a branch, and submit
4. **Improve docs** - Help make documentation clearer

### Development Setup

```bash
git clone https://github.com/crystallinecore/textstyle.git
cd textstyle
pip install -e .

# Run examples
python examples/usage_examples.py

# Run main module tests
python -m textstyle
```

---

## 📋 Requirements

- Python 3.6+
- No external dependencies

### Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux    | ✅ Full support | All features work |
| macOS    | ✅ Full support | All features work |
| Windows  | ✅ Full support | ANSI enabled automatically |

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

##  Additional Resources

- **GitHub Repository:** [github.com/crystallinecore/textstyle](https://github.com/crystallinecore/textstyle)
- **Issue Tracker:** [Report bugs or request features](https://github.com/crystallinecore/textstyle/issues)
- **PyPI Package:** [pypi.org/project/textstyle](https://pypi.org/project/textstyle)

---

## 💡 Tips & Tricks

### Disable Styling in Production

```python
import os
import textstyle as ts

if os.getenv("PRODUCTION"):
    ts.disable()
```

### Custom Logger Integration

```python
import logging
import textstyle as ts


class ColoredFormatter(logging.Formatter):
    COLORS = {"DEBUG": "bright_black", "INFO": "cyan", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "white"}

    def format(self, record):
        levelname = record.levelname
        msg = super().format(record)

        if levelname in self.COLORS:
            color = self.COLORS[levelname]
            bg = "red" if levelname == "CRITICAL" else None
            look = "bold" if levelname in ["ERROR", "CRITICAL"] else None

            parts = msg.split(levelname, 1)
            if len(parts) == 2:
                styled_level = ts.style(levelname, color=color, bg=bg, look=look)
                msg = parts[0] + styled_level + parts[1]

        return msg


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(levelname)s: %(message)s"))
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

### Performance Considerations

```python
import textstyle as ts

# For high-frequency output, disable if not needed
if not sys.stdout.isatty():
    ts.disable()

# Reuse styled strings
HEADER = ts.style("Header", color="cyan", look="bold")
ERROR = ts.style("ERROR", color="red", look="bold")

# Use format() for complex markup
# It's more efficient than multiple style() calls
```

---

## 🎓 Learning Path

1. **Beginner** - Start with `style()` function
2. **Intermediate** - Use `format()` with markup tags
3. **Advanced** - Create themes and custom styles
4. **Expert** - Build reusable components and utilities

---
<center>
Made with ❤️ by Sivaprasad Murali</center>

---
