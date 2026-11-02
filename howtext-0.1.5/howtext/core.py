import sys
import time
import math
import unicodedata

class HowText:
    def __init__(self):
        # Mapping colorful emojis to color-changeable Unicode symbols
                self.conversion_table = {
            # ── Hearts ──
            "❤️": "♥",   "❤": "♥",    "🧡": "♥",   "💛": "♥",
            "💚": "♥",   "💙": "♥",    "💜": "♥",   "🖤": "♥",
            "🤍": "♡",   "💕": "♥♥",   "💖": "♥",   "💗": "♥",
            "💘": "♥→",  "💝": "♥",    "💞": "♥♥",  "❣️": "♥",
            "❣": "♥",

            # ── Happy Faces ──
            "😀": ":D",  "😃": ":D",   "😄": "^_^", "😁": "^_^",
            "😆": "XD",  "😅": "^_^;", "🤣": "XD",  "😂": "XD",
            "🙂": ":)",  "😊": "(^◡^)","😇": "O:)", "🥰": "(♥‿♥)",
            "😍": "(♥_♥)","🤩": "(*_*)","😘": ":*", "😗": ":*",
            "😚": ":*",  "😙": ":*",   "🥲": ":')",

            # ── Neutral / Thinking ──
            "😐": ":|",  "😑": "-_-",  "🤔": "(?)", "🤗": ">^_^<",
            "🤭": ":x",  "😶": "...",  "🫡": "o7",

            # ── Sad / Angry ──
            "😢": "T_T", "😭": "(T_T)","😤": ">.<", "😠": ">:(",
            "😡": ">:(", "🥺": "(._.)","😔": "v_v", "😞": ":(",
            "😩": "DX",  "😫": "DX",   "😰": "D:",  "😱": "!!!",
            "🤮": "X(",  "🤢": "X(",

            # ── Playful / Misc Faces ──
            "😎": "B)",  "🤓": "B)",   "😈": ">:)", "👻": "☽",
            "🤡": ":o)", "😜": ";P",   "😝": "XP",  "😛": ":P",
            "🤪": ";P",  "😏": ";)",   "😒": "-_-", "🙄": "e_e",
            "😴": "zzZ", "🥱": "zzZ",  "😷": ":{",  "🤒": ":{",
            "💩": "*",   "🫠": "~_~",

            # ── Hands & Gestures ──
            "👍": "(b)", "👎": "(d)",   "👏": "◇◇", "🙏": "合",
            "🤝": "≡",  "✌️": "✌",    "✌": "✌",   "🤞": "✌",
            "🤟": "☞",  "👋": "~",     "🫶": "♥",  "💪": "(力)",
            "☝️": "↑",  "☝": "↑",     "👆": "↑",   "👇": "↓",
            "👉": "→",  "👈": "←",

            # ── Symbols & Objects ──
            "🔥": "♨",  "💀": "☠",    "⭐": "★",   "🌟": "★",
            "✨": "✧",  "⚡": "☇",    "💎": "◈",   "🚀": "»",
            "🍀": "☘",  "🎵": "♪",    "🎶": "♫",   "🎉": "※",
            "🎊": "※",  "🎯": "◎",    "🏆": "☆",   "🔔": "♪",
            "💡": "☼",  "📌": "◆",    "🔗": "∞",   "🔑": "⚷",
            "💣": "✸",  "💥": "✸",    "🌀": "◎",   "🌈": "≈",

            # ── Weather ──
            "☀️": "☼",  "☀": "☼",     "🌙": "☽",   "⛅": "☁",
            "🌧️": "☂",  "❄️": "❅",    "❄": "❅",   "💧": "☔",
            "🌊": "≋",

            # ── Status / Check ──
            "✅": "[✓]", "❌": "[✗]",  "⚠️": "[!]", "⚠": "[!]",
            "⛔": "[X]", "🚫": "⊘",   "❗": "!",    "❓": "?",
            "‼️": "!!",  "⁉️": "?!",   "💯": "100", "🆗": "[OK]",

            # ── Arrows ──
            "➡️": "→",  "⬅️": "←",   "⬆️": "↑",   "⬇️": "↓",
            "↔️": "↔",  "🔄": "↻",   "▶️": "▶",   "◀️": "◀",
            "⏩": "»",  "⏪": "«",

            # ── Animals ──
            "🐱": "=^.^=", "🐶": "U・ω・U", "🐻": "ʕ•ᴥ•ʔ",
            "🐼": "ʕ•ᴥ•ʔ", "🐸": ">_>",    "🦊": "^ω^",
            "🐰": "(·.·)",  "🐍": "~>",     "🦋": "⋇",

            # ── Flowers ──
            "🌸": "✿",  "🌺": "✿",   "🌻": "✿",   "🌹": "✿",
            "🍃": "~",

            # ── Food & Drink ──
            "🍕": "▽",  "🍔": "≡",   "☕": "c[_]",  "🍺": "⊔",
            "🍷": "⊻",  "🎂": "♨",
        }
        self._running = False

    def convert_emojis(self, text):
        """Converts fixed-color emojis to colorable unicode symbols."""
        for emoji, symbol in self.conversion_table.items():
            text = text.replace(emoji, symbol)
        return text

    def _get_color(self, step):
        """Calculates RGB rainbow color based on step."""
        r = int(math.sin(0.1 * step + 0) * 127 + 128)
        g = int(math.sin(0.1 * step + 2) * 127 + 128)
        b = int(math.sin(0.1 * step + 4) * 127 + 128)
        return f"\033[38;2;{r};{g};{b}m"

    def rainbow_print(self, text, speed=0.05):
        """Main engine for real-time rainbow animation."""
        converted_text = self.convert_emojis(text)
        step = 0
        self._running = True
        
        print(f"[HowText] Starting animation... Press Ctrl+C to stop..")
        
        try:
            while self._running:
                color = self._get_color(step)
                # Using \r to refresh the same line
                sys.stdout.write(f"\r{color}{converted_text}\033[0m")
                sys.stdout.flush()
                step += 1
                time.sleep(speed)
        except KeyboardInterrupt:
            self._running = False
            print(f"\n[HowText] Animation terminated by user.")
        except Exception as e:
            print(f"\n[HowText] Error occurred: {e}")

# Developer Test
if __name__ == "__main__":
    ht = HowText()
    ht.rainbow_print("Testing!", speed=0.03)
