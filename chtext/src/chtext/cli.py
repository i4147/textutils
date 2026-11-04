__version__ = "1.1.0"

import argparse
import hashlib
import json
import random
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

import re

import requests
from deep_translator import GoogleTranslator


class CTextAPI:
    def __init__(self):
        self.base = "https://api.ctext.org"
        self.session = requests.Session()
        self.apikey = ""
        self.language = ""
        self.remap = ""

    def _build_params(self):
        params = {}
        if self.apikey:
            params["apikey"] = self.apikey
        if self.language:
            params["if"] = self.language
        if self.remap:
            params["remap"] = self.remap
        return params

    def _call(self, endpoint, extra_params=None):
        params = self._build_params()
        if extra_params:
            params.update(extra_params)
        try:
            resp = self.session.get(f"{self.base}/{endpoint}", params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CtextAPIError(f"Network error contacting ctext.org: {e}") from e
        if not resp.text.strip():
            raise CtextAPIError("Empty response from API (possible rate limit)")
        try:
            data = resp.json()
        except ValueError as e:
            raise CtextAPIError("Invalid (non-JSON) response from API (possible rate limit or outage)") from e
        if "error" in data:
            code = data["error"].get("code", "")
            desc = data["error"].get("description", "")
            if "authentication" in code.lower() or "authentication" in desc.lower():
                raise CtextAuthError("This text requires an API key. Get one at https://ctext.org/tools/subscribe")
            raise CtextAPIError(f"API Error [{code}]: {desc}")
        return data

    def gettext(self, urn):
        return self._call("gettext", {"urn": urn})

    def searchtexts(self, title):
        return self._call("searchtexts", {"title": title})

    def getstatus(self):
        return self._call("getstatus")

    def gettextinfo(self, urn):
        return self._call("gettextinfo", {"urn": urn})

    def gettextasstring(self, urn):
        data = self.gettext(urn)
        result = ""
        if "subsections" in data:
            for sub in data["subsections"]:
                result += self.gettextasstring(sub)
        if "fulltext" in data:
            for para in data["fulltext"]:
                result += para + "\n\n"
        return result

    def gettextasparagraphlist(self, urn):
        text = self.gettextasstring(urn)
        parts = re.split(r"\n+", text)
        if parts and parts[-1] == "":
            parts.pop()
        return parts

    def setapikey(self, key):
        self.apikey = key

    def setlanguage(self, lang):
        self.language = lang

    def setremap(self, remap):
        self.remap = remap


ctapi = CTextAPI()


DATA_DIR = Path.home() / ".chtext"
DB_FILE = str(DATA_DIR / "seen_ids.sqlite")
CONFIG_FILE = Path.home() / ".ctext_config.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    legacy = Path.cwd() / "seen_ids.sqlite"
    new = Path(DB_FILE)
    if legacy.is_file() and not new.exists():
        try:
            legacy.replace(new)
        except OSError:
            pass


REQUEST_DELAY = 1.0
MAX_RETRIES = 15

FREE_BOOKS = {
    "analects": ("ctp:analects", "The Analects (論語)"),
    "mengzi": ("ctp:mengzi", "Mengzi (孟子)"),
    "dao-de-jing": ("ctp:dao-de-jing", "Dao De Jing (道德經)"),
    "mozi": ("ctp:mozi", "Mozi (墨子)"),
    "book-of-poetry": ("ctp:book-of-poetry", "Book of Poetry / Shijing (詩經)"),
}

AUTH_BOOKS = {
    "xunzi": ("ctp:xunzi", "Xunzi (荀子)"),
    "zhuangzi": ("ctp:zhuangzi", "Zhuangzi (莊子)"),
    "liezi": ("ctp:liezi", "Liezi (列子)"),
    "hanfeizi": ("ctp:hanfeizi", "Han Feizi (韓非子)"),
    "art-of-war": ("ctp:art-of-war", "Art of War (孫子兵法)"),
    "shang-jun-shu": ("ctp:shang-jun-shu", "Book of Lord Shang (商君書)"),
    "liji": ("ctp:liji", "Book of Rites (禮記)"),
    "book-of-changes": ("ctp:book-of-changes", "I Ching / Book of Changes (易經)"),
    "chun-qiu-zuo-zhuan": ("ctp:chun-qiu-zuo-zhuan", "Zuo Zhuan (左傳)"),
    "shiji": ("ctp:shiji", "Records of the Grand Historian (史記)"),
    "zhan-guo-ce": ("ctp:zhan-guo-ce", "Strategies of the Warring States (戰國策)"),
    "guanzi": ("ctp:guanzi", "Guanzi (管子)"),
    "lv-shi-chun-qiu": ("ctp:lv-shi-chun-qiu", "Lüshi Chunqiu (呂氏春秋)"),
    "huainanzi": ("ctp:huainanzi", "Huainanzi (淮南子)"),
}

AVAILABLE_BOOKS = {**FREE_BOOKS, **AUTH_BOOKS}


class CtextAPIError(Exception):
    pass


class CtextAuthError(CtextAPIError):
    pass


class Config:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.data = self._load()

    def _load(self) -> Dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "api_key": None,
            "default_book": None,
            "language": "en",
            "remap": None,
            "output_format": "full",
        }

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value
        self.save()

    def apply_to_ctext(self):
        if self.data.get("api_key"):
            ctapi.setapikey(self.data["api_key"])
        if self.data.get("language"):
            ctapi.setlanguage(self.data["language"])
        if self.data.get("remap"):
            ctapi.setremap(self.data["remap"])


class CtextLibWrapper:
    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.config.apply_to_ctext()

    def _log(self, message: str):
        if self.verbose:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def get_text(self, urn: str) -> Dict:
        self._log(f"Fetching text for URN: {urn}")
        time.sleep(REQUEST_DELAY)
        try:
            result = ctapi.gettext(urn)
            return result
        except (CtextAuthError, CtextAPIError):
            raise
        except Exception as e:
            raise CtextAPIError(str(e))

    def get_text_as_paragraphs(self, urn: str) -> List[str]:
        self._log(f"Fetching paragraphs for URN: {urn}")
        time.sleep(REQUEST_DELAY)
        try:
            result = ctapi.gettextasparagraphlist(urn)
            return result if result else []
        except Exception as e:
            raise CtextAPIError(f"Failed to get paragraphs: {e}")

    def get_text_as_string(self, urn: str) -> str:
        self._log(f"Fetching full text for URN: {urn}")
        time.sleep(REQUEST_DELAY)
        try:
            result = ctapi.gettextasstring(urn)
            return result if result else ""
        except Exception as e:
            raise CtextAPIError(f"Failed to get text: {e}")

    def get_status(self) -> Dict:
        self._log("Fetching API status")
        try:
            result = ctapi.getstatus()
            return result if result else {}
        except Exception as e:
            raise CtextAPIError(f"Failed to get status: {e}")

    def search_texts(self, query: str, urn: Optional[str] = None) -> List[Dict]:
        self._log(f"Searching for: {query} in {urn or 'all texts'}")
        time.sleep(REQUEST_DELAY)
        try:
            result = ctapi.searchtexts(query)
            return result if result else []
        except Exception as e:
            raise CtextAPIError(f"Search failed: {e}")

    def get_available_books(self) -> Dict[str, tuple]:
        return AVAILABLE_BOOKS


class TranslatorWrapper:
    def __init__(self, verbose: bool = False):
        self.translator = GoogleTranslator(source="zh-CN", target="en")
        self.verbose = verbose

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return "[Empty text]"
        try:
            result = self.translator.translate(text)
            return result if result else "[Translation unavailable]"
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Translation error: {e}", file=sys.stderr)
            return f"[Translation Error: {type(e).__name__}]"


class StateTracker:
    def __init__(self, db_path: str = DB_FILE):
        if db_path == DB_FILE:
            _ensure_data_dir()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_id TEXT UNIQUE NOT NULL,
                    book_urn TEXT,
                    chapter_urn TEXT,
                    text_preview TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_seen(self, unique_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM seen_quotes WHERE unique_id = ?", (unique_id,))
            return cursor.fetchone() is not None

    def mark_seen(self, unique_id: str, book_urn: str = "", chapter_urn: str = "", text_preview: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO seen_quotes (unique_id, book_urn, chapter_urn, text_preview) VALUES (?, ?, ?, ?)",
                    (unique_id, book_urn, chapter_urn, text_preview[:100]),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass

    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM seen_quotes")
            total = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT book_urn, COUNT(*) as count FROM seen_quotes GROUP BY book_urn ORDER BY count DESC"
            )
            by_book = cursor.fetchall()

            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM seen_quotes")
            date_range = cursor.fetchone()

            return {
                "total": total,
                "by_book": by_book,
                "first_seen": date_range[0],
                "last_seen": date_range[1],
            }

    def reset(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM seen_quotes")
            conn.commit()


class QuoteFetcher:
    def __init__(self, config: Config, verbose: bool = False):
        self.api = CtextLibWrapper(config, verbose=verbose)
        self.translator = TranslatorWrapper(verbose=verbose)
        self.state = StateTracker()
        self.verbose = verbose

    def _log(self, message: str):
        if self.verbose:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def _get_book_urn(self, book_key: Optional[str], free_only: bool = False) -> str:
        if book_key:
            if book_key not in AVAILABLE_BOOKS:
                available = ", ".join(AVAILABLE_BOOKS.keys())
                raise ValueError(f"Unknown book '{book_key}'. Available: {available}")
            return AVAILABLE_BOOKS[book_key][0]
        pool = FREE_BOOKS if free_only else AVAILABLE_BOOKS
        return random.choice(list(pool.values()))[0]

    def _generate_unique_id(self, chapter_urn: str, paragraph_index: int, text: str) -> str:
        content = f"{chapter_urn}:{paragraph_index}:{hashlib.md5(text.encode()).hexdigest()[:8]}"
        return content

    def fetch_quote(self, book_key: Optional[str] = None, unique: bool = False) -> Optional[Dict]:
        max_attempts = MAX_RETRIES if unique else 3

        for attempt in range(max_attempts):
            try:
                book_urn = self._get_book_urn(book_key)
                self._log(f"Attempt {attempt + 1}: Fetching from {book_urn}")

                data = self.api.get_text(book_urn)

                if isinstance(data, dict) and "subsections" in data and data["subsections"]:
                    chapter_urn = random.choice(data["subsections"])
                    self._log(f"Selected chapter: {chapter_urn}")
                    data = self.api.get_text(chapter_urn)
                elif isinstance(data, dict):
                    chapter_urn = book_urn
                else:
                    chapter_urn = book_urn

                if not isinstance(data, dict) or "fulltext" not in data or not data["fulltext"]:
                    self._log(f"No fulltext in response for {chapter_urn}")
                    continue

                fulltext = data["fulltext"]
                title = data.get("title", "Unknown")

                valid_paragraphs = []
                for i, p in enumerate(fulltext):
                    if isinstance(p, str) and p.strip():
                        valid_paragraphs.append((i, p.strip()))
                    elif isinstance(p, dict) and p.get("text", "").strip():
                        valid_paragraphs.append((i, p["text"].strip()))

                if not valid_paragraphs:
                    self._log(f"No valid paragraphs in {chapter_urn}")
                    continue

                para_index, quote_text = random.choice(valid_paragraphs)
                unique_id = self._generate_unique_id(chapter_urn, para_index, quote_text)

                if unique and self.state.is_seen(unique_id):
                    self._log(f"Quote already seen: {unique_id}")
                    continue

                quote = {
                    "text": quote_text,
                    "book_urn": book_urn,
                    "chapter_urn": chapter_urn,
                    "chapter_title": title,
                    "paragraph_index": para_index,
                    "unique_id": unique_id,
                }

                if unique:
                    self.state.mark_seen(unique_id, book_urn, chapter_urn, quote_text)

                return quote

            except CtextAPIError as e:
                print(f"API Error: {e}", file=sys.stderr)
                if attempt < max_attempts - 1:
                    self._log("Retrying...")
                    continue
                return None
            except Exception as e:
                self._log(f"Unexpected error: {e}")
                if attempt < max_attempts - 1:
                    continue
                return None

        return None

    def format_quote(self, quote: Dict, include_translation: bool = True, format_style: str = "full") -> str:
        if format_style == "json":
            output = quote.copy()
            if include_translation:
                output["translation"] = self.translator.translate(quote["text"])
            return json.dumps(output, ensure_ascii=False, indent=2)

        if format_style == "minimal":
            return quote["text"]

        lines = []

        if format_style == "full":
            lines.append("=" * 50)

            book_name = quote["book_urn"]
            for key, (urn, display) in AVAILABLE_BOOKS.items():
                if urn == quote["book_urn"]:
                    book_name = display
                    break

            lines.append(f"📚 {book_name}")
            lines.append(f"📖 Chapter: {quote['chapter_title']}")
            lines.append("-" * 50)

        lines.append(f"「{quote['text']}」")

        if include_translation:
            if format_style == "full":
                lines.append("-" * 50)
            translation = self.translator.translate(quote["text"])
            lines.append(f"Translation: {translation}")

        if format_style == "full":
            lines.append("=" * 50)

        return "\n".join(lines)

    def fetch_short_quote(
        self, book_key: Optional[str] = None, unique: bool = True, max_chars: int = 80
    ) -> Optional[Dict]:
        max_attempts = MAX_RETRIES if unique else 5

        for attempt in range(max_attempts):
            try:
                book_urn = self._get_book_urn(book_key, free_only=(book_key is None))
                self._log(f"Short-quote attempt {attempt + 1}: {book_urn}")

                data = self.api.get_text(book_urn)

                if isinstance(data, dict) and "subsections" in data and data["subsections"]:
                    chapter_urn = random.choice(data["subsections"])
                    self._log(f"Selected chapter: {chapter_urn}")
                    data = self.api.get_text(chapter_urn)
                elif isinstance(data, dict):
                    chapter_urn = book_urn
                else:
                    chapter_urn = book_urn

                if not isinstance(data, dict) or "fulltext" not in data or not data["fulltext"]:
                    continue

                title = data.get("title", "Unknown")
                candidates = _extract_short_segments(data["fulltext"], max_chars)

                if not candidates:
                    self._log("No short segments found in this chapter")
                    continue

                random.shuffle(candidates)

                for para_idx, segment in candidates:
                    uid = self._generate_unique_id(chapter_urn, para_idx, segment)
                    if unique and self.state.is_seen(uid):
                        continue

                    translation = self.translator.translate(segment)

                    quote = {
                        "text": segment,
                        "translation": translation,
                        "book_urn": book_urn,
                        "chapter_urn": chapter_urn,
                        "chapter_title": title,
                        "paragraph_index": para_idx,
                        "unique_id": uid,
                    }
                    if unique:
                        self.state.mark_seen(uid, book_urn, chapter_urn, segment)
                    return quote

            except CtextAuthError as e:
                print(f"Auth required: {e}", file=sys.stderr)
                return None
            except CtextAPIError as e:
                self._log(f"API error: {e}")
                if attempt < max_attempts - 1:
                    continue
                return None
            except Exception as e:
                self._log(f"Unexpected error: {e}")
                if attempt < max_attempts - 1:
                    continue
                return None

        return None


def _extract_short_segments(fulltext: List, max_chars: int = 80) -> List[tuple]:
    splitter = re.compile(r"(?<=[。！？])")
    results = []

    for i, para in enumerate(fulltext):
        text = para.strip() if isinstance(para, str) else ""
        if isinstance(para, dict):
            text = para.get("text", "").strip()
        if not text or len(text) < 4:
            continue

        if len(text) <= max_chars:
            results.append((i, text))
            continue

        sentences = [s.strip() for s in splitter.split(text) if s.strip()]
        sentences = [s for s in sentences if len(s) >= 4]

        for s in sentences:
            if len(s) <= max_chars:
                results.append((i, s))

        for j in range(len(sentences) - 1):
            pair = sentences[j] + sentences[j + 1]
            if len(pair) <= max_chars:
                results.append((i, pair))

    return results


def _format_english_quote(quote: Dict, with_chinese: bool = False) -> str:
    book_name = quote["book_urn"]
    for _key, (urn, display) in AVAILABLE_BOOKS.items():
        if urn == quote["book_urn"]:
            book_name = display
            break

    lines = [f'"{quote["translation"]}"']
    lines.append(f"  -- {book_name}, {quote['chapter_title']}")
    if with_chinese:
        lines.append(f"     {quote['text']}")
    return "\n".join(lines)


def cmd_random(args, fetcher: QuoteFetcher):
    quote = fetcher.fetch_quote(book_key=args.book, unique=False)

    if not quote:
        print("Error: Could not retrieve a quote. Please try again.", file=sys.stderr)
        return 1

    print(fetcher.format_quote(quote, include_translation=not args.no_translate, format_style=args.format))
    return 0


def cmd_unique(args, fetcher: QuoteFetcher):
    quote = fetcher.fetch_quote(book_key=args.book, unique=True)

    if not quote:
        stats = fetcher.state.get_stats()
        print(f"Error: Could not find a unique quote after {MAX_RETRIES} attempts.", file=sys.stderr)
        print(
            f"You have seen {stats['total']} quotes. Consider using 'stats --reset' to clear history.",
            file=sys.stderr,
        )
        return 1

    print(fetcher.format_quote(quote, include_translation=not args.no_translate, format_style=args.format))
    return 0


def cmd_batch(args, fetcher: QuoteFetcher):
    output_file = args.output or f"quotes_{int(time.time())}.txt"
    count = args.count

    print(f"Generating {count} unique quotes...")
    print(f"Output file: {output_file}")
    print()

    success_count = 0
    quotes_data = []

    with open(output_file, "w", encoding="utf-8") as f:
        for i in range(count):
            quote = fetcher.fetch_quote(book_key=args.book, unique=True)

            if quote:
                if args.format == "json":
                    quote_with_trans = quote.copy()
                    if not args.no_translate:
                        quote_with_trans["translation"] = fetcher.translator.translate(quote["text"])
                    quotes_data.append(quote_with_trans)
                else:
                    formatted = fetcher.format_quote(
                        quote, include_translation=not args.no_translate, format_style="full"
                    )
                    f.write(formatted + "\n\n")
                success_count += 1
                print(f"  [{success_count}/{count}] ✓ Saved quote from {quote['chapter_title']}")
            else:
                print(f"  [{i + 1}/{count}] ✗ Could not find unique quote")

        if args.format == "json":
            f.write(json.dumps(quotes_data, ensure_ascii=False, indent=2))

    print()
    print(f"Done! Saved {success_count}/{count} quotes to {output_file}")
    return 0 if success_count > 0 else 1


def cmd_list(args, fetcher: QuoteFetcher):
    print("Available Books:")
    print("=" * 60)

    print("\n  FREE (no API key needed):")
    print("-" * 40)
    for key, (urn, display) in FREE_BOOKS.items():
        print(f"  {key:22} {display}")

    print("\n  REQUIRES API KEY (ctext.org/tools/subscribe):")
    print("-" * 40)
    for key, (urn, display) in AUTH_BOOKS.items():
        print(f"  {key:22} {display}")

    print("\n" + "=" * 60)
    print("\nUse --book <key> to select a specific book.")
    print("Example: chtext generate --book analects")
    return 0


def cmd_stats(args, fetcher: QuoteFetcher):
    if args.reset:
        fetcher.state.reset()
        print("✓ Quote history has been reset.")
        return 0

    stats = fetcher.state.get_stats()

    print("Quote Statistics")
    print("=" * 40)
    print(f"Total quotes seen: {stats['total']}")

    if stats["first_seen"]:
        print(f"First seen: {stats['first_seen']}")
        print(f"Last seen: {stats['last_seen']}")

    if stats["by_book"]:
        print("\nBy Book:")
        print("-" * 40)
        for book_urn, count in stats["by_book"]:
            display = book_urn
            for key, (urn, name) in AVAILABLE_BOOKS.items():
                if urn == book_urn:
                    display = name
                    break
            print(f"  {display}: {count}")

    print("=" * 40)
    return 0


def cmd_search(args, fetcher: QuoteFetcher, config: Config):
    query = args.query
    book_key = args.book

    print(f"Searching for: '{query}'")
    if book_key:
        if book_key not in AVAILABLE_BOOKS:
            print(f"Error: Unknown book '{book_key}'", file=sys.stderr)
            return 1
        urn = AVAILABLE_BOOKS[book_key][0]
        print(f"In book: {AVAILABLE_BOOKS[book_key][1]}")
    else:
        urn = None
        print("In: all texts")
    print()

    try:
        results = fetcher.api.search_texts(query, urn)

        if not results:
            print("No results found.")
            return 0

        if args.format == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Found {len(results)} result(s):")
            print("-" * 50)
            for i, result in enumerate(results[: args.limit], 1):
                if isinstance(result, dict):
                    text = result.get("text", result.get("passage", str(result)))
                    title = result.get("title", "")
                    urn = result.get("urn", "")
                    print(f"\n[{i}] {title}")
                    print(f"    URN: {urn}")
                    print(f"    「{text[:200]}{'...' if len(text) > 200 else ''}」")
                else:
                    print(f"\n[{i}] {result}")

        return 0
    except CtextAPIError as e:
        print(f"Search error: {e}", file=sys.stderr)
        return 1


def cmd_browse(args, fetcher: QuoteFetcher):
    book_key = args.book

    if book_key not in AVAILABLE_BOOKS:
        print(f"Error: Unknown book '{book_key}'", file=sys.stderr)
        print("Use 'list' command to see available books.")
        return 1

    urn, display_name = AVAILABLE_BOOKS[book_key]

    print(f"📚 {display_name}")
    print(f"   URN: {urn}")
    print("=" * 50)

    try:
        data = fetcher.api.get_text(urn)

        if not isinstance(data, dict):
            print("Error: Unexpected response format", file=sys.stderr)
            return 1

        if "subsections" in data and data["subsections"]:
            print(f"\n📖 Chapters ({len(data['subsections'])}):")
            print("-" * 40)
            for i, sub_urn in enumerate(data["subsections"][: args.limit], 1):
                try:
                    sub_data = fetcher.api.get_text(sub_urn)
                    title = sub_data.get("title", sub_urn) if isinstance(sub_data, dict) else sub_urn
                except Exception:
                    title = sub_urn
                print(f"  {i:3}. {title}")
                print(f"       URN: {sub_urn}")

            if len(data["subsections"]) > args.limit:
                print(f"\n  ... and {len(data['subsections']) - args.limit} more chapters")
                print("  Use --limit to show more")

        elif "fulltext" in data and data["fulltext"]:
            print(f"\n📝 Full Text ({len(data['fulltext'])} paragraphs):")
            print("-" * 40)
            for i, para in enumerate(data["fulltext"][:5], 1):
                text = para if isinstance(para, str) else para.get("text", "")
                preview = text[:80] + "..." if len(text) > 80 else text
                print(f"  {i}. 「{preview}」")

            if len(data["fulltext"]) > 5:
                print(f"\n  ... and {len(data['fulltext']) - 5} more paragraphs")

        else:
            print("\nNo content available (may require authentication)")
            print("Tip: Set an API key with 'config --set-apikey YOUR_KEY'")

        return 0

    except CtextAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_download(args, fetcher: QuoteFetcher):
    book_key = args.book

    if book_key not in AVAILABLE_BOOKS:
        print(f"Error: Unknown book '{book_key}'", file=sys.stderr)
        return 1

    urn, display_name = AVAILABLE_BOOKS[book_key]
    output_file = args.output or f"{book_key}_{int(time.time())}.txt"

    print(f"Downloading: {display_name}")
    print(f"Output file: {output_file}")
    print()

    try:
        if args.format == "string":
            text = fetcher.api.get_text_as_string(urn)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {display_name}\n")
                f.write(f"# URN: {urn}\n")
                f.write(f"# Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            print("✓ Saved as continuous text")
        else:
            paragraphs = fetcher.api.get_text_as_paragraphs(urn)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {display_name}\n")
                f.write(f"# URN: {urn}\n")
                f.write(f"# Downloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Paragraphs: {len(paragraphs)}\n\n")
                for i, para in enumerate(paragraphs, 1):
                    f.write(f"[{i}] {para}\n\n")
            print(f"✓ Saved {len(paragraphs)} paragraphs")

        print(f"✓ Done: {output_file}")
        return 0

    except CtextAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_status(args, fetcher: QuoteFetcher, config: Config):
    print("API Status")
    print("=" * 40)

    api_key = config.get("api_key")
    print(f"API Key: {'[SET]' if api_key else '[NOT SET]'}")
    print(f"Language: {config.get('language', 'en')}")
    print(f"Remap: {config.get('remap') or 'None (Traditional Chinese)'}")
    print()

    try:
        status = fetcher.api.get_status()

        if isinstance(status, dict):
            print("Server Status:")
            print("-" * 40)
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"Status: {status}")

    except CtextAPIError as e:
        print(f"Could not fetch status: {e}", file=sys.stderr)
        print("\nNote: Some features require an API key or account.")
        print("Visit https://ctext.org/tools/subscribe for more info.")

    print("=" * 40)
    return 0


def cmd_config(args, config: Config):
    if args.show:
        print("Current Configuration")
        print("=" * 40)
        print(f"Config file: {config.config_path}")
        print("-" * 40)
        for key, value in config.data.items():
            display_value = "[SET]" if key == "api_key" and value else value
            print(f"  {key}: {display_value}")
        print("=" * 40)
        return 0

    if args.set_apikey is not None:
        key = args.set_apikey.strip()
        if key.lower() == "none" or key == "":
            config.set("api_key", None)
            print("✓ API key cleared")
        else:
            config.set("api_key", key)
            print("✓ API key set")
        return 0

    if args.set_language:
        config.set("language", args.set_language)
        print(f"✓ Language set to: {args.set_language}")
        return 0

    if args.set_remap:
        if args.set_remap.lower() == "none":
            config.set("remap", None)
            print("✓ Remap disabled (Traditional Chinese)")
        else:
            config.set("remap", args.set_remap)
            print(f"✓ Remap set to: {args.set_remap}")
        return 0

    if args.set_default_book:
        if args.set_default_book.lower() == "none":
            config.set("default_book", None)
            print("✓ Default book cleared")
        elif args.set_default_book in AVAILABLE_BOOKS:
            config.set("default_book", args.set_default_book)
            print(f"✓ Default book set to: {args.set_default_book}")
        else:
            print(f"Error: Unknown book '{args.set_default_book}'", file=sys.stderr)
            return 1
        return 0

    print("Use 'config --show' to view current settings")
    print("Use 'config --set-apikey KEY' to set API key")
    print("Use 'config --set-language LANG' to set language (en/zh)")
    print("Use 'config --set-remap MODE' to set character mapping (gb/none)")
    return 0


def cmd_generate(args, fetcher: QuoteFetcher):
    count = getattr(args, "count", 1)
    book_key = getattr(args, "book", None)
    with_chinese = getattr(args, "with_chinese", False)
    output_file = getattr(args, "output", None)
    fmt = getattr(args, "format", "text")

    quotes_collected = []

    if count == 1 and not output_file:
        quote = fetcher.fetch_short_quote(book_key=book_key, unique=True)
        if not quote:
            print(
                "Could not find a short quote. Try again or specify a different --book.",
                file=sys.stderr,
            )
            return 1
        if fmt == "json":
            print(json.dumps(quote, ensure_ascii=False, indent=2))
        else:
            print(_format_english_quote(quote, with_chinese=with_chinese))
        return 0

    target = output_file or f"english_quotes_{int(time.time())}.txt"
    print(f"Generating {count} short English quotes...")
    if output_file:
        print(f"Output: {target}")
    print()

    for i in range(count):
        quote = fetcher.fetch_short_quote(book_key=book_key, unique=True)
        if quote:
            quotes_collected.append(quote)
            preview = quote["translation"][:60]
            print(f"  [{len(quotes_collected)}/{count}] {preview}...")
        else:
            print(f"  [{i + 1}/{count}] (skipped - no unique quote found)")

    if not quotes_collected:
        print("\nNo quotes could be generated.", file=sys.stderr)
        return 1

    with open(target, "w", encoding="utf-8") as f:
        if fmt == "json":
            f.write(json.dumps(quotes_collected, ensure_ascii=False, indent=2))
        else:
            for q in quotes_collected:
                f.write(_format_english_quote(q, with_chinese=with_chinese))
                f.write("\n\n")

    print(f"\nDone! {len(quotes_collected)}/{count} quotes saved to {target}")
    return 0


def _configure_console_encoding():
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass


def main():
    _configure_console_encoding()
    parser = argparse.ArgumentParser(
        prog="chtext",
        description="chtext - Classical Chinese Text Quote Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  chtext generate                          Get one short English quote
  chtext generate --book dao-de-jing       Short quote from Dao De Jing
  chtext generate --count 20               Generate 20 quotes to a file
  chtext generate --with-chinese           Include original Chinese text
  chtext random                            Random quote (full paragraph)
  chtext random --book analects            Random Analects quote
  chtext list                              Show all available books
  chtext search --query "仁"               Search for a Chinese term
  chtext browse analects                   Explore book structure
  chtext config --set-apikey YOUR_KEY      Unlock all books with an API key

full documentation: https://github.com/3D3Q3/chtext
        """,
    )

    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose/debug output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    gen_parser = subparsers.add_parser(
        "generate", help="Generate short English quotes (1-3 sentences) from classical texts"
    )
    gen_parser.add_argument(
        "--book",
        "-b",
        choices=list(AVAILABLE_BOOKS.keys()),
        help="Specific book to draw from (default: random)",
    )
    gen_parser.add_argument("--count", "-n", type=int, default=1, help="Number of quotes to generate (default: 1)")
    gen_parser.add_argument("--output", "-o", help="Output file (auto-created when --count > 1)")
    gen_parser.add_argument(
        "--with-chinese", action="store_true", help="Include original Chinese text below each quote"
    )
    gen_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    random_parser = subparsers.add_parser("random", help="Get a random quote from classical Chinese texts")
    random_parser.add_argument(
        "--book",
        "-b",
        choices=list(AVAILABLE_BOOKS.keys()),
        help="Specific book to fetch from (use 'list' to see options)",
    )
    random_parser.add_argument("--no-translate", action="store_true", help="Skip English translation")
    random_parser.add_argument(
        "--format",
        "-f",
        choices=["full", "minimal", "json"],
        default="full",
        help="Output format (default: full)",
    )

    unique_parser = subparsers.add_parser("unique", help="Get a unique quote (not seen before)")
    unique_parser.add_argument("--book", "-b", choices=list(AVAILABLE_BOOKS.keys()), help="Specific book to fetch from")
    unique_parser.add_argument("--no-translate", action="store_true", help="Skip English translation")
    unique_parser.add_argument(
        "--format",
        "-f",
        choices=["full", "minimal", "json"],
        default="full",
        help="Output format (default: full)",
    )

    batch_parser = subparsers.add_parser("batch", help="Generate multiple unique quotes to a file")
    batch_parser.add_argument("--count", "-n", type=int, required=True, help="Number of quotes to generate (required)")
    batch_parser.add_argument("--output", "-o", help="Output filename (default: quotes_<timestamp>.txt)")
    batch_parser.add_argument("--book", "-b", choices=list(AVAILABLE_BOOKS.keys()), help="Specific book to fetch from")
    batch_parser.add_argument("--no-translate", action="store_true", help="Skip English translation")
    batch_parser.add_argument(
        "--format",
        "-f",
        choices=["full", "json"],
        default="full",
        help="Output format (default: full)",
    )

    subparsers.add_parser("list", help="List available books")

    stats_parser = subparsers.add_parser("stats", help="Show quote history statistics")
    stats_parser.add_argument("--reset", action="store_true", help="Reset/clear all quote history")

    search_parser = subparsers.add_parser("search", help="Search for passages containing specific text")
    search_parser.add_argument("--query", "-q", required=True, help="Search query (Chinese characters)")
    search_parser.add_argument(
        "--book", "-b", choices=list(AVAILABLE_BOOKS.keys()), help="Limit search to specific book"
    )
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="Maximum results to show (default: 10)")
    search_parser.add_argument(
        "--format",
        "-f",
        choices=["full", "json"],
        default="full",
        help="Output format (default: full)",
    )

    browse_parser = subparsers.add_parser("browse", help="Explore book structure and chapters")
    browse_parser.add_argument("book", choices=list(AVAILABLE_BOOKS.keys()), help="Book to browse")
    browse_parser.add_argument("--limit", "-l", type=int, default=20, help="Maximum chapters to show (default: 20)")

    download_parser = subparsers.add_parser("download", help="Download full text of a book to file")
    download_parser.add_argument("book", choices=list(AVAILABLE_BOOKS.keys()), help="Book to download")
    download_parser.add_argument("--output", "-o", help="Output filename (default: <book>_<timestamp>.txt)")
    download_parser.add_argument(
        "--format",
        "-f",
        choices=["paragraphs", "string"],
        default="paragraphs",
        help="Output format (default: paragraphs)",
    )

    subparsers.add_parser("status", help="Show API status and rate limit info")

    config_parser = subparsers.add_parser("config", help="Manage configuration and API key")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--set-apikey", metavar="KEY", help="Set API key (use 'none' to clear)")
    config_parser.add_argument("--set-language", choices=["en", "zh"], help="Set interface language")
    config_parser.add_argument(
        "--set-remap",
        metavar="MODE",
        help="Set character remap ('gb' for simplified, 'none' for traditional)",
    )
    config_parser.add_argument("--set-default-book", metavar="BOOK", help="Set default book for random quotes")

    args = parser.parse_args()

    config = Config()

    fetcher = QuoteFetcher(config, verbose=args.verbose)

    commands = {
        "generate": lambda: cmd_generate(args, fetcher),
        "random": lambda: cmd_random(args, fetcher),
        "unique": lambda: cmd_unique(args, fetcher),
        "batch": lambda: cmd_batch(args, fetcher),
        "list": lambda: cmd_list(args, fetcher),
        "stats": lambda: cmd_stats(args, fetcher),
        "search": lambda: cmd_search(args, fetcher, config),
        "browse": lambda: cmd_browse(args, fetcher),
        "download": lambda: cmd_download(args, fetcher),
        "status": lambda: cmd_status(args, fetcher, config),
        "config": lambda: cmd_config(args, config),
    }

    if args.command in commands:
        try:
            sys.exit(commands[args.command]())
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(130)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if args.verbose:
                import traceback

                traceback.print_exc()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
