"""
Tests for about_singapore_law fragment creation logic.
"""

import pytest

from resources.about_singapore_law import create_content_fragments


def test_simple_numbered_paragraphs():
    """Test basic numbered paragraphs create separate fragments."""
    content_parts = [
        {
            "text": "1.1.1      This is the first numbered paragraph with some content.",
            "type": "paragraph",
            "original_text": "1.1.1      This is the first numbered paragraph with some content.",
        },
        {
            "text": "1.1.2      This is the second numbered paragraph with different content.",
            "type": "paragraph",
            "original_text": "1.1.2      This is the second numbered paragraph with different content.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2
    assert fragments[0]["id"] == "test_chapter_1.1.1"
    assert "first numbered paragraph" in fragments[0]["content_text"]

    assert fragments[1]["id"] == "test_chapter_1.1.2"
    assert "second numbered paragraph" in fragments[1]["content_text"]


def test_header_attached_to_next_numbered_paragraph():
    """Test that headers are attached to the following numbered paragraph."""
    content_parts = [
        {
            "text": "SECTION 1 INTRODUCTION",
            "type": "heading",
            "original_text": "SECTION 1 INTRODUCTION",
        },
        {
            "text": "1.1.1      The Singapore legal system is a rich tapestry of laws.",
            "type": "paragraph",
            "original_text": "1.1.1      The Singapore legal system is a rich tapestry of laws.",
        },
        {"text": "SECTION 2 HISTORY", "type": "heading", "original_text": "SECTION 2 HISTORY"},
        {
            "text": "1.2.1      From its founding by Sir Thomas Stamford Raffles.",
            "type": "paragraph",
            "original_text": "1.2.1      From its founding by Sir Thomas Stamford Raffles.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2

    # First fragment should include header + numbered paragraph
    assert fragments[0]["id"] == "test_chapter_1.1.1"
    assert "SECTION 1 INTRODUCTION" in fragments[0]["content_text"]
    assert "Singapore legal system" in fragments[0]["content_text"]

    # Second fragment should include header + numbered paragraph
    assert fragments[1]["id"] == "test_chapter_1.2.1"
    assert "SECTION 2 HISTORY" in fragments[1]["content_text"]
    assert "Sir Thomas Stamford Raffles" in fragments[1]["content_text"]


def test_multiple_headers_before_numbered_paragraph():
    """Test multiple headers are all attached to the next numbered paragraph."""
    content_parts = [
        {
            "text": "SECTION 1 INTRODUCTION",
            "type": "heading",
            "original_text": "SECTION 1 INTRODUCTION",
        },
        {
            "text": "Overview of Legal System",
            "type": "heading",
            "original_text": "Overview of Legal System",
        },
        {"text": "Historical Context", "type": "heading", "original_text": "Historical Context"},
        {
            "text": "1.1.1      The Singapore legal system is comprehensive.",
            "type": "paragraph",
            "original_text": "1.1.1      The Singapore legal system is comprehensive.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 1
    content = fragments[0]["content_text"]
    assert "SECTION 1 INTRODUCTION" in content
    assert "Overview of Legal System" in content
    assert "Historical Context" in content
    assert "Singapore legal system is comprehensive" in content


def test_indented_paragraphs_attach_to_previous_fragment():
    """Test that indented paragraphs attach to the previous numbered paragraph."""
    content_parts = [
        {
            "text": "1.1.1      This is a numbered paragraph with some legal content.",
            "type": "paragraph",
            "original_text": "1.1.1      This is a numbered paragraph with some legal content.",
        },
        {
            "text": "    This is an indented continuation paragraph that explains more.",
            "type": "paragraph",
            "original_text": "<p>    This is an indented continuation paragraph that explains more.</p>",
        },
        {
            "text": "    This is another indented paragraph with additional details.",
            "type": "paragraph",
            "original_text": "<p>    This is another indented paragraph with additional details.</p>",
        },
        {
            "text": "1.1.2      This is the next numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.2      This is the next numbered paragraph.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2

    # First fragment should include numbered paragraph + indented content
    first_content = fragments[0]["content_text"]
    assert "numbered paragraph with some legal content" in first_content
    assert "indented continuation paragraph" in first_content
    assert "additional details" in first_content

    # Second fragment should be separate
    assert fragments[1]["id"] == "test_chapter_1.1.2"
    assert "next numbered paragraph" in fragments[1]["content_text"]


def test_headers_and_indented_paragraphs_combined():
    """Test complex scenario with headers before and indented content after."""
    content_parts = [
        {
            "text": "SECTION 1 INTRODUCTION",
            "type": "heading",
            "original_text": "SECTION 1 INTRODUCTION",
        },
        {"text": "Legal Framework", "type": "heading", "original_text": "Legal Framework"},
        {
            "text": "1.1.1      The Singapore legal system operates under specific principles.",
            "type": "paragraph",
            "original_text": "1.1.1      The Singapore legal system operates under specific principles.",
        },
        {
            "text": "    These principles include fairness and justice.",
            "type": "paragraph",
            "original_text": "<p>    These principles include fairness and justice.</p>",
        },
        {
            "text": "    The system also emphasizes efficiency.",
            "type": "paragraph",
            "original_text": "<p>    The system also emphasizes efficiency.</p>",
        },
        {"text": "SECTION 2 HISTORY", "type": "heading", "original_text": "SECTION 2 HISTORY"},
        {
            "text": "1.2.1      Singapore's legal development has been extensive.",
            "type": "paragraph",
            "original_text": "1.2.1      Singapore's legal development has been extensive.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2

    # First fragment: headers + numbered + indented
    first_content = fragments[0]["content_text"]
    assert "SECTION 1 INTRODUCTION" in first_content
    assert "Legal Framework" in first_content
    assert "operates under specific principles" in first_content
    assert "principles include fairness" in first_content
    assert "emphasizes efficiency" in first_content

    # Second fragment: header + numbered
    second_content = fragments[1]["content_text"]
    assert "SECTION 2 HISTORY" in second_content
    assert "legal development has been extensive" in second_content


def test_remaining_headers_attach_to_last_fragment():
    """Test that headers at the end attach to the last fragment."""
    content_parts = [
        {
            "text": "1.1.1      This is the only numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.1      This is the only numbered paragraph.",
        },
        {"text": "Final Notes", "type": "heading", "original_text": "Final Notes"},
        {
            "text": "Additional Information",
            "type": "heading",
            "original_text": "Additional Information",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 1
    content = fragments[0]["content_text"]
    assert "only numbered paragraph" in content
    assert "Final Notes" in content
    assert "Additional Information" in content


def test_skip_short_paragraphs():
    """Test that very short paragraphs are skipped."""
    content_parts = [
        {
            "text": "Hi",
            "type": "paragraph",
            "original_text": "Hi",
        },  # Too short (< 5 chars), should be skipped
        {
            "text": "1.1.1      This is a proper numbered paragraph with sufficient content.",
            "type": "paragraph",
            "original_text": "1.1.1      This is a proper numbered paragraph with sufficient content.",
        },
        {"text": "x", "type": "paragraph", "original_text": "x"},  # Too short, should be skipped
        {
            "text": "1.1.2      This is another proper numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.2      This is another proper numbered paragraph.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2
    assert fragments[0]["id"] == "test_chapter_1.1.1"
    assert fragments[1]["id"] == "test_chapter_1.1.2"


def test_empty_paragraphs_list():
    """Test handling of empty paragraphs list."""
    fragments = create_content_fragments([], "test_chapter")
    assert len(fragments) == 0


def test_no_numbered_paragraphs():
    """Test handling when there are only headers and no numbered paragraphs."""
    content_parts = [
        {
            "text": "SECTION 1 INTRODUCTION",
            "type": "heading",
            "original_text": "SECTION 1 INTRODUCTION",
        },
        {
            "text": "This is just a header section",
            "type": "heading",
            "original_text": "This is just a header section",
        },
        {"text": "More header content", "type": "heading", "original_text": "More header content"},
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")
    assert len(fragments) == 0


def test_fragment_order_and_char_count():
    """Test that fragments have correct order and character counts."""
    content_parts = [
        {"text": "Header One", "type": "heading", "original_text": "Header One"},
        {
            "text": "1.1.1      First numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.1      First numbered paragraph.",
        },
        {
            "text": "    Indented content for first.",
            "type": "paragraph",
            "original_text": "<p>    Indented content for first.</p>",
        },
        {
            "text": "1.1.2      Second numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.2      Second numbered paragraph.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2

    # Check fragment order
    assert fragments[0]["fragment_order"] == 0
    assert fragments[1]["fragment_order"] == 1

    # Check character counts are calculated correctly
    assert fragments[0]["char_count"] == len(fragments[0]["content_text"])
    assert fragments[1]["char_count"] == len(fragments[1]["content_text"])

    # First fragment should be longer due to header and indented content
    assert fragments[0]["char_count"] > fragments[1]["char_count"]


def test_various_numbering_patterns():
    """Test different numbering patterns work correctly."""
    content_parts = [
        {
            "text": "1.1.1      First pattern.",
            "type": "paragraph",
            "original_text": "1.1.1      First pattern.",
        },
        {
            "text": "1.2.15     Second pattern with larger numbers.",
            "type": "paragraph",
            "original_text": "1.2.15     Second pattern with larger numbers.",
        },
        {
            "text": "2.10.3     Third pattern with different section.",
            "type": "paragraph",
            "original_text": "2.10.3     Third pattern with different section.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 3
    assert fragments[0]["id"] == "test_chapter_1.1.1"
    assert fragments[1]["id"] == "test_chapter_1.2.15"
    assert fragments[2]["id"] == "test_chapter_2.10.3"


def test_indented_content_only_with_exact_spacing():
    """Test that only paragraphs with exactly 4 spaces are treated as indented."""
    content_parts = [
        {
            "text": "1.1.1      Main numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.1      Main numbered paragraph.",
        },
        {
            "text": "    Four spaces - should be indented content.",
            "type": "paragraph",
            "original_text": "<p>    Four spaces - should be indented content.</p>",
        },
        {
            "text": "  Two spaces - should be header for next.",
            "type": "paragraph",
            "original_text": "  Two spaces - should be header for next.",
        },
        {
            "text": "        Eight spaces - should be header for next.",
            "type": "paragraph",
            "original_text": "        Eight spaces - should be header for next.",
        },
        {
            "text": "1.1.2      Next numbered paragraph.",
            "type": "paragraph",
            "original_text": "1.1.2      Next numbered paragraph.",
        },
    ]

    fragments = create_content_fragments(content_parts, "test_chapter")

    assert len(fragments) == 2

    # First fragment should only include the 4-space indented content
    first_content = fragments[0]["content_text"]
    assert "Main numbered paragraph" in first_content
    assert "Four spaces - should be indented" in first_content

    # Second fragment should include the other content as headers
    second_content = fragments[1]["content_text"]
    assert "Two spaces - should be header" in second_content
    assert "Eight spaces - should be header" in second_content
    assert "Next numbered paragraph" in second_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
