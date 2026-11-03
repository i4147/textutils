import textstyle as ts
import time
import sys


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_basic_styling():
    print_section("1. BASIC STYLING WITH style()")
    print(ts.style("Error message", color="red"))
    print(ts.style("Success message", color="green"))
    print(ts.style("Warning message", color="yellow"))
    print(ts.style("Info message", color="blue"))
    print(ts.style("Bold Red Error", color="red", look="bold"))
    print(ts.style("Italic Blue Info", color="blue", look="italic"))
    print(ts.style("Underlined Warning", color="yellow", look="underline"))
    print(ts.style("Critical Alert", color="white", bg="red", look="bold"))
    print(ts.style("Success Badge", color="black", bg="green", look="bold"))
    print(ts.style("Info Banner", color="white", bg="blue"))
    print(ts.style("Bold + Underline", color="magenta", look=["bold", "underline"]))


def demo_hex_rgb_colors():
    print_section("2. HEX AND RGB COLORS")
    print(ts.style("Brand Color #FF5733", color="#FF5733", look="bold"))
    print(ts.style("Ocean Blue #0077BE", color="#0077BE"))
    print(ts.style("Lime Green #32CD32", color="#32CD32"))
    print(ts.style("Red #F00", color="#F00", look="bold"))
    print(ts.style("Blue #00F", color="#00F", look="bold"))
    print(ts.style("RGB Red (255, 0, 0)", color=(255, 0, 0)))
    print(ts.style("RGB Purple (128, 0, 128)", color=(128, 0, 128), look="italic"))
    print(ts.style("RGB Orange (255, 165, 0)", color=(255, 165, 0)))
    print(ts.style("Dark Theme", color="#00FF00", bg="#1A1A1A", look="bold"))
    print(ts.style("Light Theme", color="#1A1A1A", bg="#F0F0F0"))


def demo_format_tags():
    print_section("3. FORMAT WITH MARKUP TAGS")
    print(ts.format("This is <red>red</red>, <green>green</green>, and <blue>blue</blue>"))
    print(ts.format("Use <bold>bold</bold>, <italic>italic</italic>, and <underline>underline</underline>"))
    print(ts.format("<red><bold>Bold Red Text</bold></red>"))
    print(ts.format("<blue>Blue with <underline>underlined part</underline></blue>"))
    print(ts.format("Normal <bg_red><white>ALERT</white></bg_red> text"))
    print(ts.format("<bg_green><black>SUCCESS</black></bg_green> operation complete"))
    print(ts.format("Brand: <#FF5733>Orange</#FF5733> and <#00BFFF>Sky Blue</#00BFFF>"))
    print(
        ts.format(
            "<bold>Status Report:</bold> <green>Connected</green> | <yellow>Warning</yellow> | <red>2 Errors</red>"
        )
    )


def demo_custom_styles():
    print_section("4. CUSTOM STYLES")
    ts.create("error", color="red", look="bold")
    ts.create("success", color="green", look="bold")
    ts.create("warning", color="yellow", look="bold")
    ts.create("info", color="cyan")
    ts.create("highlight", color="black", bg="yellow")
    ts.create("badge", color="white", bg="blue", look="bold")
    print(ts.format("<error>ERROR:</error> Connection failed"))
    print(ts.format("<success>SUCCESS:</success> File saved"))
    print(ts.format("<warning>WARNING:</warning> Low disk space"))
    print(ts.format("<info>INFO:</info> Processing request"))
    print(ts.format("Please <highlight>note</highlight> this important information"))
    print(ts.format("<badge>NEW</badge> Feature available"))
    print(ts.error("Direct error style function"))
    print(ts.success("Direct success style function"))


def demo_themes():
    print_section("5. THEME SYSTEM")
    print(ts.style("Dark Theme", look="bold"))
    ts.set_theme("dark")
    print(ts.format("<error>Error:</error> Database connection failed"))
    print(ts.format("<success>Success:</success> Server started"))
    print(ts.format("<warning>Warning:</warning> Memory usage high"))
    print(ts.format("<info>Info:</info> Logged in as admin"))
    print(ts.format("<debug>Debug:</debug> Variable x = 42"))
    print(ts.format("<critical>CRITICAL</critical> System failure"))
    print("\n" + ts.style("Light Theme", look="bold"))
    ts.set_theme("light")
    print(ts.format("<error>Error:</error> Database connection failed"))
    print(ts.format("<success>Success:</success> Server started"))
    print(ts.format("<warning>Warning:</warning> Memory usage high"))
    print("\n" + ts.style("Custom Brand Theme", look="bold"))
    ts.set_theme({
        "primary": {"color": "#007AFF", "look": "bold"},
        "secondary": {"color": "#5856D6"},
        "danger": {"color": "white", "bg": "#FF3B30", "look": "bold"},
        "accent": {"color": "#FF9500", "look": "bold"},
        "muted": {"color": "bright_black"},
    })
    print(ts.format("<primary>Primary Action</primary>"))
    print(ts.format("<secondary>Secondary Action</secondary>"))
    print(ts.format("<danger>Delete Account</danger>"))
    print(ts.format("<accent>Special Offer!</accent>"))
    print(ts.format("<muted>Less important details</muted>"))


def demo_utility_functions():
    print_section("6. UTILITY FUNCTIONS")
    markup = "<red>Hello</red> <bold>World</bold> <underline>!</underline>"
    print(f"Original: {markup}")
    print(f"Stripped: {ts.strip(markup)}")
    styled = ts.style("Styled Text", color="red", look="bold")
    print(f"\nStyled: {styled}")
    print(f"Cleaned: {ts.clean(styled)}")
    text = ts.style("Hello", color="red", look="bold")
    print(f"\nText with ANSI: {text}")
    print(f"len() returns: {len(text)}")
    print(f"ts.length() returns: {ts.length(text)}")
    print("\n" + ts.style("Styling enabled", color="green"))
    ts.disable()
    print(ts.style("Styling disabled (plain text)", color="red"))
    ts.enable()
    print(ts.style("Styling re-enabled", color="green"))


def demo_temporary_styles():
    print_section("7. TEMPORARY STYLES")
    print("Before temporary style")
    with ts.temporary("temp", color="magenta", look="italic"):
        print(ts.format("<temp>This style exists only in this context</temp>"))
        print(ts.format("You can use <temp>temp</temp> multiple times here"))
    print("After context - temp style is deleted:")
    print(ts.format("<temp>This will be plain text</temp>"))
    with ts.temporary("outer", color="blue", look="bold"):
        print(ts.format("<outer>Outer style</outer>"))
        with ts.temporary("inner", color="red", look="italic"):
            print(ts.format("<outer>Outer with <inner>inner</inner></outer>"))
        print(ts.format("<outer>Inner style is gone</outer>"))


def demo_logging_system():
    print_section("8. REAL-WORLD: LOGGING SYSTEM")
    ts.set_theme({
        "timestamp": {"color": "bright_black"},
        "debug": {"color": "bright_black"},
        "info": {"color": "cyan"},
        "success": {"color": "green", "look": "bold"},
        "warning": {"color": "yellow", "look": "bold"},
        "error": {"color": "red", "look": "bold"},
        "critical": {"color": "white", "bg": "red", "look": "bold"},
    })

    def log(level, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(ts.format(f"<timestamp>[{timestamp}]</timestamp> <{level}>{level.upper():<8}</{level}> {message}"))

    log("debug", "Application started")
    log("info", "Loading configuration from config.yaml")
    log("success", "Database connection established")
    log("warning", "Cache miss for key 'user:123'")
    log("error", "Failed to send email to user@example.com")
    log("critical", "Out of memory - shutting down")


def demo_cli_menu():
    print_section("9. REAL-WORLD: CLI MENU")
    ts.set_theme({
        "title": {"color": "cyan", "look": "bold"},
        "option": {"color": "green"},
        "key": {"color": "yellow", "look": "bold"},
        "desc": {"color": "white"},
        "footer": {"color": "bright_black"},
    })
    menu = """
<title>╔═══════════════════════════════════╗</title>
<title>║     APPLICATION MAIN MENU         ║</title>
<title>╚═══════════════════════════════════╝</title>

<key>[1]</key> <option>Create New Project</option>
     <desc>Start a new project from scratch</desc>

<key>[2]</key> <option>Open Existing Project</option>
     <desc>Load a project from disk</desc>

<key>[3]</key> <option>Settings</option>
     <desc>Configure application preferences</desc>

<key>[4]</key> <option>Help & Documentation</option>
     <desc>View user manual and tutorials</desc>

<key>[Q]</key> <option>Quit</option>
     <desc>Exit the application</desc>

<footer>────────────────────────────────────</footer>
<footer>Enter your choice: </footer>"""
    print(ts.format(menu))


def demo_progress_indicator():
    print_section("10. REAL-WORLD: PROGRESS INDICATOR")
    ts.set_theme({
        "bar_filled": {"color": "green", "look": "bold"},
        "bar_empty": {"color": "bright_black"},
        "percent": {"color": "cyan", "look": "bold"},
        "status": {"color": "white"},
    })

    def show_progress(current, total, status):
        percent = int((current / total) * 100)
        filled = int((current / total) * 30)
        empty = 30 - filled
        bar = ts.format(f"<bar_filled>{'█' * filled}</bar_filled><bar_empty>{'░' * empty}</bar_empty>")
        line = ts.format(f"{bar} <percent>{percent:3d}%</percent> <status>{status}</status>")
        print(f"\r{line}", end="", flush=True)

    print("Downloading file...")
    for i in range(101):
        if i < 30:
            status = "Connecting..."
        elif i < 80:
            status = "Downloading..."
        else:
            status = "Finalizing..."
        show_progress(i, 100, status)
        time.sleep(0.02)
    print("\n" + ts.format("<bar_filled>✓ Download complete!</bar_filled>"))


def demo_data_table():
    print_section("11. REAL-WORLD: DATA TABLE")
    ts.set_theme({
        "header": {"color": "cyan", "look": "bold"},
        "high": {"color": "green", "look": "bold"},
        "medium": {"color": "yellow"},
        "low": {"color": "red"},
        "border": {"color": "bright_black"},
    })
    data = [
        {"name": "Server-1", "status": "high", "cpu": "23%", "mem": "45%"},
        {"name": "Server-2", "status": "medium", "cpu": "67%", "mem": "78%"},
        {"name": "Server-3", "status": "low", "cpu": "94%", "mem": "95%"},
        {"name": "Server-4", "status": "high", "cpu": "12%", "mem": "34%"},
    ]
    print(ts.format("<border>┌────────────┬──────────┬──────┬──────┐</border>"))
    print(
        ts.format(
            "<border>│</border> <header>Server</header>     "
            "<border>│</border> <header>Status</header>   "
            "<border>│</border> <header>CPU</header>  "
            "<border>│</border> <header>Mem</header>  "
            "<border>│</border>"
        )
    )
    print(ts.format("<border>├────────────┼──────────┼──────┼──────┤</border>"))
    for row in data:
        status_icon = "●" if row["status"] == "high" else "◐" if row["status"] == "medium" else "○"
        print(
            ts.format(
                f"<border>│</border> {row['name']:<10} "
                f"<border>│</border> <{row['status']}>{status_icon} {row['status'].title():<6}</{row['status']}> "
                f"<border>│</border> {row['cpu']:<4} "
                f"<border>│</border> {row['mem']:<4} "
                f"<border>│</border>"
            )
        )
    print(ts.format("<border>└────────────┴──────────┴──────┴──────┘</border>"))


def demo_code_syntax():
    print_section("12. REAL-WORLD: CODE SYNTAX HIGHLIGHTING")
    ts.set_theme({
        "keyword": {"color": "magenta", "look": "bold"},
        "function": {"color": "blue", "look": "bold"},
        "string": {"color": "green"},
        "comment": {"color": "bright_black"},
        "number": {"color": "cyan"},
        "operator": {"color": "yellow"},
    })
    code = """
<keyword>def</keyword> <function>calculate_total</function>(<keyword>items</keyword>):
    <comment># Calculate total price with tax</comment>
    <keyword>total</keyword> <operator>=</operator> <number>0</number>
    <keyword>for</keyword> <keyword>item</keyword> <keyword>in</keyword> <keyword>items</keyword>:
        <keyword>total</keyword> <operator>+=</operator> <keyword>item</keyword>[<string>'price'</string>]
    <keyword>tax</keyword> <operator>=</operator> <keyword>total</keyword> <operator>*</operator> <number>0.08</number>
    <keyword>return</keyword> <keyword>total</keyword> <operator>+</operator> <keyword>tax</keyword>
"""
    print(ts.format(code))


def demo_git_style_output():
    print_section("13. REAL-WORLD: GIT-STYLE STATUS OUTPUT")
    ts.set_theme({
        "branch": {"color": "cyan", "look": "bold"},
        "added": {"color": "green"},
        "modified": {"color": "yellow"},
        "deleted": {"color": "red"},
        "untracked": {"color": "red"},
        "label": {"color": "white", "look": "bold"},
    })
    output = """
On branch <branch>main</branch>
Your branch is up to date with 'origin/main'.

<label>Changes to be committed:</label>
  <added>new file:   src/main.py</added>
  <added>new file:   README.md</added>

<label>Changes not staged for commit:</label>
  <modified>modified:   config.yaml</modified>
  <modified>modified:   requirements.txt</modified>

<label>Untracked files:</label>
  <untracked>temp/</untracked>
  <untracked>cache.db</untracked>
"""
    print(ts.format(output))


def demo_dashboard():
    print_section("14. REAL-WORLD: SYSTEM DASHBOARD")
    ts.set_theme({
        "title": {"color": "cyan", "look": "bold"},
        "label": {"color": "bright_black"},
        "good": {"color": "green", "look": "bold"},
        "warn": {"color": "yellow", "look": "bold"},
        "critical": {"color": "red", "look": "bold"},
        "metric": {"color": "white", "look": "bold"},
    })
    dashboard = """
<title>╔════════════════════════════════════════════════════════╗</title>
<title>║              SYSTEM DASHBOARD                          ║</title>
<title>╚════════════════════════════════════════════════════════╝</title>

<label>CPU Usage:</label>      [<good>███████████</good><warn>██</warn>░░░░░░░░] <metric>45%</metric>
<label>Memory:</label>         [<good>██████████████</good><warn>███</warn>░░░] <metric>68%</metric>
<label>Disk Space:</label>     [<good>██████████████████</good><critical>██</critical>] <metric>89%</metric>
<label>Network:</label>        [<good>█████████████████████</good>] <good>Online</good>

<title>Active Services:</title>
  <good>✓</good> Web Server      <label>(nginx)</label>
  <good>✓</good> Database        <label>(postgresql)</label>
  <good>✓</good> Cache           <label>(redis)</label>
  <critical>✗</critical> Email Service   <label>(postfix)</label>

<title>Recent Alerts:</title>
  <critical>[CRITICAL]</critical> Disk space above 85%
  <warn>[WARNING]</warn>  High memory usage detected
  <good>[INFO]</good>     Backup completed successfully
"""
    print(ts.format(dashboard))


def demo_validation_messages():
    print_section("15. REAL-WORLD: FORM VALIDATION")
    ts.set_theme({
        "valid": {"color": "green"},
        "invalid": {"color": "red"},
        "field": {"color": "cyan", "look": "bold"},
        "hint": {"color": "bright_black"},
    })
    validation = """
<field>Email:</field> user@example.com <valid>✓ Valid</valid>
<field>Password:</field> ********** <valid>✓ Strong</valid>
<field>Username:</field> ab <invalid>✗ Too short (minimum 3 characters)</invalid>
<field>Phone:</field> 123-456-7890 <valid>✓ Valid format</valid>
<field>Age:</field> 200 <invalid>✗ Must be between 1 and 120</invalid>

<hint>Please correct the errors above before submitting.</hint>
"""
    print(ts.format(validation))


def demo_all_colors():
    print_section("16. COLOR REFERENCE")
    print(ts.style("Standard Colors:", look="bold"))
    for color in ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]:
        print(f"  {ts.style(color.ljust(15), color=color)} {ts.style(f'bg_{color}'.ljust(15), bg=color)}")
    print("\n" + ts.style("Bright Colors:", look="bold"))
    for color in [
        "bright_black",
        "bright_red",
        "bright_green",
        "bright_yellow",
        "bright_blue",
        "bright_magenta",
        "bright_cyan",
        "bright_white",
    ]:
        base_color = color.replace("bright_", "")
        print(f"  {ts.style(color.ljust(15), color=color)} {ts.style(f'bg_{color}'.ljust(15), bg=base_color)}")


def main():
    print(ts.style("╔" + "═" * 68 + "╗", color="cyan", look="bold"))
    print(ts.style("║" + " " * 68 + "║", color="cyan", look="bold"))
    print(
        ts.style("║" + "  TEXTSTYLE LIBRARY - COMPREHENSIVE USAGE EXAMPLES".center(68) + "║", color="cyan", look="bold")
    )
    print(ts.style("║" + " " * 68 + "║", color="cyan", look="bold"))
    print(ts.style("╚" + "═" * 68 + "╝", color="cyan", look="bold"))
    demo_basic_styling()
    demo_hex_rgb_colors()
    demo_format_tags()
    demo_custom_styles()
    demo_themes()
    demo_utility_functions()
    demo_temporary_styles()
    demo_logging_system()
    demo_cli_menu()
    demo_progress_indicator()
    demo_data_table()
    demo_code_syntax()
    demo_git_style_output()
    demo_dashboard()
    demo_validation_messages()
    demo_all_colors()
    print_section("COMPLETE")
    print(
        ts.format(
            "<green><bold>✓ All demonstrations completed successfully!</bold></green>\n"
            "<bright_black>Check the output above for examples you can use in your projects.</bright_black>"
        )
    )


if __name__ == "__main__":
    main()
