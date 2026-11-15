"""The local preview presents existing native captures without obsolete controls."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'img':
            self.images.append(dict(attrs))


class ReadonlyPreviewTest(unittest.TestCase):
    def test_entry_pages_and_native_captures(self):
        for relative in ('prototype/index.html', 'prototype/current/index.html'):
            parser = PreviewParser()
            page = ROOT / relative
            parser.feed(page.read_text())
            self.assertFalse({'script', 'select', 'input', 'button'} & set(parser.tags))
            if relative == 'prototype/index.html':
                self.assertEqual(len(parser.images), 2)
                for img in parser.images:
                    self.assertTrue(img.get('alt'))
                    self.assertTrue((page.parent / img['src']).is_file())
                self.assertIn('not physical-device or Store acceptance', page.read_text())


if __name__ == '__main__':
    unittest.main()
