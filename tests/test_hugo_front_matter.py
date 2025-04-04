import pytest
from pathlib import Path
from wx.hugo_front_matter import HugoFrontMatter


@pytest.fixture
def sample_key_value_front_matter():
    return """title="Test Article"
subtitle="A test article"
tags=["test", "example"]
categories=["Test"]
---
# Test Content
This is a test article."""


@pytest.fixture
def sample_colon_front_matter():
    return """title: Test Article
subtitle: A test article
tags: [test, example]
categories: [Test]
---
# Test Content
This is a test article."""


def test_parse_key_value_format(sample_key_value_front_matter):
    parser = HugoFrontMatter(sample_key_value_front_matter)
    front_matter = parser.parse()

    assert front_matter["title"] == "Test Article"
    assert front_matter["subtitle"] == "A test article"
    assert front_matter["tags"] == ["test", "example"]
    assert front_matter["categories"] == ["Test"]


def test_parse_colon_format(sample_colon_front_matter):
    parser = HugoFrontMatter(sample_colon_front_matter)
    front_matter = parser.parse()

    assert front_matter["title"] == "Test Article"
    assert front_matter["subtitle"] == "A test article"
    assert front_matter["tags"] == ["test", "example"]
    assert front_matter["categories"] == ["Test"]


def test_convert_to_key_value_format(sample_colon_front_matter):
    parser = HugoFrontMatter(sample_colon_front_matter)
    parser.parse()
    result = parser.to_string()

    assert 'title="Test Article"' in result
    assert 'subtitle="A test article"' in result
    assert 'tags=["test", "example"]' in result
    assert 'categories=["Test"]' in result


def test_validate_required_fields():
    content = """subtitle="A test article"
tags=["test"]
---
# Content"""

    parser = HugoFrontMatter(content)
    with pytest.raises(ValueError) as exc:
        parser.validate()
    assert "Missing required field: title" in str(exc.value)


def test_get_content_without_front_matter(sample_key_value_front_matter):
    parser = HugoFrontMatter(sample_key_value_front_matter)
    parser.parse()
    content = parser.get_content()

    assert content.strip() == "# Test Content\nThis is a test article."


def test_invalid_front_matter():
    content = "This is just content without front matter"
    parser = HugoFrontMatter(content)
    with pytest.raises(ValueError) as exc:
        parser.parse()
    assert "No front matter found in content" in str(exc.value)


def test_empty_front_matter():
    content = """---
# Just content"""
    parser = HugoFrontMatter(content)
    front_matter = parser.parse()
    assert front_matter == {}
    assert parser.get_content().strip() == "# Just content"


def test_mixed_list_formats():
    content = """tags=["test"]
categories: [Test, Demo]
mixed=[1, "two", 3]
---
# Content"""
    parser = HugoFrontMatter(content)
    front_matter = parser.parse()
    assert front_matter["tags"] == ["test"]
    assert front_matter["categories"] == ["Test", "Demo"]
    assert front_matter["mixed"] == [1, "two", 3]


def test_invalid_list_format():
    content = """tags=[invalid list]
---
# Content"""
    parser = HugoFrontMatter(content)
    front_matter = parser.parse()
    assert front_matter["tags"] == ["invalid", "list"]
