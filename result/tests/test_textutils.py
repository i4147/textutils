import random
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner
from textutils import (
    TextFile,
    SimpleSentenceTokenizer,
    SpongeString,
    leetspeak,
    levenshtein_distance,
    levenshtein_similarity,
    lcs_distance,
    lcs_similarity,
    search_files,
)
from textutils.cli import app


class TextTests(unittest.TestCase):
    def test_distances(self):
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("", "abc"), 3)
        self.assertEqual(levenshtein_similarity("", ""), 1.0)
        self.assertEqual(lcs_distance("abc", "ac"), 1)
        self.assertEqual(lcs_similarity("", ""), 1.0)
        self.assertAlmostEqual(lcs_similarity("abc", "ac"), 0.8)
        self.assertEqual(levenshtein_distance("å", "a"), 1)

    def test_transformations(self):
        self.assertEqual(leetspeak("Hello!"), "H3LL0!")
        self.assertEqual(str(SpongeString("Hi  THERE", 10, rng=random.Random(0))), "HI  THERE")
        with self.assertRaises(ValueError):
            SpongeString("abc", 11)
        self.assertEqual(SimpleSentenceTokenizer()("One! Two? Last"), ["One!", "Two?", "Last"])
        self.assertEqual(SimpleSentenceTokenizer("]")("a] b"), ["a]", "b"])

    def test_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sub").mkdir()
            path = root / "sub" / "a.txt"
            path.write_text("hello\nworld hello\n", encoding="utf-8")
            (root / "other.md").write_text("hello", encoding="utf-8")
            expected = [(1, "hello"), (2, "world hello")]
            self.assertEqual(TextFile(path).search("hello"), expected)
            self.assertEqual(list(search_files(root, "hello")), [(path, expected)])
            (root / "bad.txt").write_bytes(b"\xff")
            with self.assertRaises(UnicodeDecodeError):
                list(search_files(root, "hello"))

    def test_cli(self):
        runner = CliRunner()
        result = runner.invoke(app, ["distance", "kitten", "sitting"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.stdout.strip(), "3")
        self.assertEqual(runner.invoke(app, ["leet", "hello"]).stdout.strip(), "H3LL0")


if __name__ == "__main__":
    unittest.main()
