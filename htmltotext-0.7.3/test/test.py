#!/usr/bin/env python
#
# Copyright (C) 2007 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
r"""test.py: Test htmltotext module."""

import unittest

import htmltotext


class TestHtmlToText(unittest.TestCase):
    def test_extract_body(self):
        """Test extracting the body text."""
        html = "<html><body><p>Hello  World</p></body></html>"
        assert htmltotext.extract(html).title == ""
        assert htmltotext.extract(html).description == ""
        assert htmltotext.extract(html).content == "Hello World"

    def test_default_charset(self):
        """Test a conversion supplying a string, which should use the default
        character set.

        """
        html = "<title>foo\xa3</title>"
        assert htmltotext.extract(html).title == "foo£"

    def test_unicode_input(self):
        """Test supplying a unicode string as input."""
        html = '<meta http-equiv="content-type" content="charset=latin1"/><title>foo\xa3</title>'
        assert htmltotext.extract(html).title == "foo£"

    def test_meta_content_type(self):
        """Test supplying a meta http-equiv tag to set the character set."""
        html = '<meta http-equiv="content-type" content="charset=utf8"/><title>foo\xc2\xa3</title>'
        assert htmltotext.extract(html).title == "foo£"

    def test_meta_content_type(self):
        """Test supplying a meta http-equiv tag to set the character set
        incorrectly.

        Will raise an error when trying to convert the output to unicode.

        """
        html = '<meta http-equiv="content-type" content="charset=utf8"/><title>foo\xa3</title>'
        assert htmltotext.extract(html).title == "foo"
        assert htmltotext.extract(html).badly_encoded == True

    def test_meta_description(self):
        """Test supplying a meta description tag."""
        html = '<meta name="description" content="desc"/><title>foo</title><body>body</body>'
        assert htmltotext.extract(html).title == "foo"
        assert htmltotext.extract(html).description == "desc"
        assert htmltotext.extract(html).keywords == ""
        assert htmltotext.extract(html).indexing_allowed == True
        assert htmltotext.extract(html).badly_encoded == False

    def test_meta_description(self):
        """Test supplying a meta description tag."""
        html = '<meta name="robots" content="noindex"/><title>foo</title><body>body</body>'
        assert htmltotext.extract(html).title == ""
        assert htmltotext.extract(html).description == ""
        assert htmltotext.extract(html).keywords == ""
        assert htmltotext.extract(html).indexing_allowed == False

    def test_link1(self):
        """Test parsing some links."""
        html = '<title>Here it <p/>is</title><body><foo class="1" id=top>body <a href="bar">link content</a><b/><a href="/foo2">2</p><a class="foo" href="http://bar.com/foo3">3</a> end body</foo><a href="test"><i>mo<em>re</em></i><b>test</a></body>'
        parsed = htmltotext.extract(html)
        assert parsed.title == "Here it is"
        assert parsed.description == ""
        assert parsed.keywords == ""
        assert parsed.indexing_allowed == True
        assert parsed.content == "body link content2 3 end bodymoretest"
        assert len(parsed.links) == 4

        assert parsed.links[0].target == "bar"
        assert parsed.links[0].text == "link content"
        assert parsed.links[0].para == "body link content2"
        assert parsed.links[0].start_pos == 4
        assert parsed.links[1].target == "/foo2"
        assert parsed.links[1].text == "2"
        assert parsed.links[1].para == "body link content2"
        assert parsed.links[1].start_pos == 17
        assert parsed.links[2].target == "http://bar.com/foo3"
        assert parsed.links[2].text == "3"
        assert parsed.links[2].para == "3 end bodymoretest"
        assert parsed.links[2].start_pos == 18
        assert parsed.links[3].target == "test"
        assert parsed.links[3].text == "moretest"
        assert parsed.links[3].para == "3 end bodymoretest"
        assert parsed.links[3].start_pos == 29

        assert len(parsed.links[0].parent_tags) == 3
        assert parsed.links[0].parent_tags[0].name == "body"
        assert parsed.links[0].parent_tags[0].cls == ""
        assert parsed.links[0].parent_tags[0].id == ""
        assert parsed.links[0].parent_tags[1].name == "foo"
        assert parsed.links[0].parent_tags[1].cls == "1"
        assert parsed.links[0].parent_tags[1].id == "top"

        assert parsed.links[0].parent_tags[-1].name == "a"
        assert parsed.links[0].parent_tags[-1].cls == ""
        assert parsed.links[1].parent_tags[-1].name == "a"
        assert parsed.links[1].parent_tags[-1].cls == ""
        assert parsed.links[2].parent_tags[-1].name == "a"
        assert parsed.links[2].parent_tags[-1].cls == "foo"
        assert parsed.links[3].parent_tags[-1].name == "a"
        assert parsed.links[3].parent_tags[-1].cls == ""

        assert parsed.links[0].child_tags == []
        assert parsed.links[1].child_tags == []
        assert parsed.links[2].child_tags == []
        assert len(parsed.links[3].child_tags) == 3
        assert parsed.links[3].child_tags[0].name == "i"
        assert parsed.links[3].child_tags[1].name == "em"
        assert parsed.links[3].child_tags[2].name == "b"

        assert parsed.parastarts == [0, 18, 37]

    def test_link2(self):
        """Test parsing some links interspersed with tags which don't close."""
        html = '<body><div><a href="a1"></a><br></div><a href="a2"></a><br><a href="a3"></a></body>'
        parsed = htmltotext.extract(html)
        assert [t.name for t in parsed.links[0].parent_tags] == ["body", "div", "a"]
        assert [t.name for t in parsed.links[1].parent_tags] == ["body", "a"]
        assert [t.name for t in parsed.links[2].parent_tags] == ["body", "a"]


def suite():
    return unittest.makeSuite(TestHtmlToText)


def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())


if __name__ == "__main__":
    test()
