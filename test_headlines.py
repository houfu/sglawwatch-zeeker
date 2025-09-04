"""
Tests for the headlines resource.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resources.headlines import (
    convert_date_to_iso,
    fetch_data,
    get_hash_id,
    get_jina_reader_content,
    get_summary,
    process_entry,
)


class TestUtilityFunctions:
    """Test utility functions in the headlines module."""

    def test_get_hash_id_basic(self):
        """Test basic hash ID generation."""
        elements = ["2025-05-16", "Meeting Notes"]
        result = get_hash_id(elements)
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hash length

        # Same input should produce same hash
        result2 = get_hash_id(elements)
        assert result == result2

    def test_get_hash_id_custom_delimiter(self):
        """Test hash ID generation with custom delimiter."""
        elements = ["user123", "login", "192.168.1.1"]
        result1 = get_hash_id(elements, delimiter=":")
        result2 = get_hash_id(elements, delimiter="|")
        assert result1 != result2

    def test_get_hash_id_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="At least one element is required"):
            get_hash_id([])

    def test_convert_date_to_iso_standard_format(self):
        """Test date conversion with standard format."""
        date_str = "08 May 2025 00:01:00"
        result = convert_date_to_iso(date_str)
        assert result == "2025-05-08T00:01:00"

    def test_convert_date_to_iso_abbreviated_format(self):
        """Test date conversion with abbreviated month format."""
        date_str = "08 May 2025 00:01:00"
        result = convert_date_to_iso(date_str)
        assert result == "2025-05-08T00:01:00"

    def test_convert_date_to_iso_invalid_format_returns_current(self):
        """Test that invalid date format returns current datetime."""
        with patch("resources.headlines.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "2025-08-11T12:00:00"
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime.side_effect = ValueError("Invalid format")

            result = convert_date_to_iso("invalid date")
            assert result == "2025-08-11T12:00:00"

    def test_should_skip_advertisements(self):
        """Test that advertisements are properly filtered out."""
        from resources.headlines import _should_skip_entry
        from datetime import datetime

        current_date = datetime.now()
        
        # Test ADV: format
        adv_entry_1 = {
            "title": "ADV: Some advertisement content",
            "published": "04 Sep 2025 00:01:00"
        }
        
        # Test ADV JLP: format (space after ADV)
        adv_entry_2 = {
            "title": "ADV JLP: Starting an Action (Disputes)",
            "published": "04 Sep 2025 00:01:00"
        }
        
        # Test normal article (should not be skipped for advertisement)
        normal_entry = {
            "title": "Singapore, India to launch roadmap on cooperation",
            "published": "04 Sep 2025 00:01:00"
        }
        
        # Test advertisement filtering
        should_skip_1, reason_1 = _should_skip_entry(adv_entry_1, current_date, None, set())
        assert should_skip_1 is True
        assert reason_1 == "advertisement"
        
        should_skip_2, reason_2 = _should_skip_entry(adv_entry_2, current_date, None, set())
        assert should_skip_2 is True
        assert reason_2 == "advertisement"
        
        # Normal entry should not be skipped for advertisement
        should_skip_normal, reason_normal = _should_skip_entry(normal_entry, current_date, None, set())
        # It might be skipped for other reasons, but not for advertisement
        if should_skip_normal:
            assert reason_normal != "advertisement"


class TestAsyncFunctions:
    """Test async functions in the headlines module."""

    @pytest.mark.asyncio
    async def test_get_jina_reader_content_missing_token(self):
        """Test Jina reader with missing API token."""
        with patch.dict("os.environ", {}, clear=True):
            result = await get_jina_reader_content("https://example.com")
            assert result == ""

    @pytest.mark.asyncio
    async def test_get_jina_reader_content_success(self):
        """Test successful Jina reader content fetch."""
        mock_response = MagicMock()
        mock_response.text = "Article content here"

        with patch.dict("os.environ", {"JINA_API_TOKEN": "test-token"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = await get_jina_reader_content("https://example.com")
                assert result == "Article content here"

    @pytest.mark.asyncio
    async def test_get_summary_missing_api_key(self):
        """Test summary generation with missing OpenAI API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = await get_summary("Some article text")
            assert result == ""

    @pytest.mark.asyncio
    async def test_get_summary_success(self):
        """Test successful summary generation."""
        mock_response = MagicMock()
        mock_response.output_text = "This is a summary"

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.AsyncOpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_client.responses.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                result = await get_summary("Article text to summarize")
                assert result == "This is a summary"

    @pytest.mark.asyncio
    async def test_process_entry_success(self):
        """Test successful entry processing."""
        entry = {
            "published": "08 May 2025 00:01:00",
            "title": "Test Article",
            "link": "https://example.com",
            "author": "Test Author",
            "category": "Legal News",
        }

        with patch(
            "resources.headlines.get_jina_reader_content", new_callable=AsyncMock
        ) as mock_jina:
            with patch("resources.headlines.get_summary", new_callable=AsyncMock) as mock_summary:
                mock_jina.return_value = "Article content"
                mock_summary.return_value = "Article summary"

                result = await process_entry(entry)

                assert result is not None
                assert result["title"] == "Test Article"
                assert result["author"] == "Test Author"
                assert result["category"] == "Legal News"
                assert result["source_link"] == "https://example.com"
                assert result["text"] == "Article content"
                assert result["summary"] == "Article summary"
                assert "id" in result
                assert "date" in result
                assert "imported_on" in result

    @pytest.mark.asyncio
    async def test_process_entry_exception_handling(self):
        """Test entry processing with exception."""
        entry = {"published": "invalid date", "title": "Test Article"}

        result = await process_entry(entry)
        # The function handles invalid dates gracefully and returns data with fallback values
        assert result is not None
        assert result["title"] == "Test Article"
        # The date should be converted to current time as fallback
        assert "date" in result
        assert result["date"] is not None

    @pytest.mark.asyncio
    async def test_fetch_data_basic(self):
        """Test basic fetch_data functionality."""
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "published": "10 August 2025 00:01:00",  # Recent date
                "title": "Test Article 1",
                "link": "https://example1.com",
                "author": "Author 1",
                "category": "Legal News",
            },
            {
                "published": "09 August 2025 00:01:00",
                "title": "ADV: Advertisement",
                "link": "https://example2.com",
            },
        ]

        with patch("feedparser.parse", return_value=mock_feed):
            with patch("resources.headlines.process_entry", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = {
                    "id": "test123",
                    "title": "Test Article 1",
                    "text": "Content",
                    "summary": "Summary",
                }

                result = await fetch_data(None)

                # Should skip ADV entries, so only 1 call to process_entry
                assert mock_process.call_count == 1
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_data_with_existing_table(self):
        """Test fetch_data with existing table and metadata."""
        mock_table = MagicMock()
        mock_table.name = "headlines"

        mock_db = MagicMock()
        mock_db.table_names.return_value = ["_zeeker_updates", "headlines"]
        mock_table.db = mock_db

        mock_updates_table = MagicMock()
        mock_updates_table.get.return_value = {"last_updated": "2025-08-09T00:00:00"}  # Recent date
        mock_db.__getitem__.return_value = mock_updates_table

        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "published": "11 August 2025 00:01:00",  # After last_updated
                "title": "New Article",
                "link": "https://example1.com",
                "author": "Author 1",
                "category": "Legal News",
            },
            {
                "published": "08 August 2025 00:01:00",  # Before last_updated
                "title": "Old Article",
                "link": "https://example2.com",
            },
        ]

        with patch("feedparser.parse", return_value=mock_feed):
            with patch("resources.headlines.process_entry", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = {"id": "test123", "title": "New Article"}

                await fetch_data(mock_table)

                # Should only process the new article
                assert mock_process.call_count == 1

    @pytest.mark.asyncio
    async def test_process_entry_problematic_url_handling(self):
        """Test that problematic URLs are handled gracefully."""
        from resources.headlines import process_entry

        # Entry with a problematic URL (store.lawnet.com)
        test_entry = {
            "id": "test_lawnet",
            "category": "Legal",
            "title": "Test LawNet Article",
            "link": "https://store.lawnet.com/jlp-starting-an-action.html?utm_source=slw_edm",
            "author": "Legal Team",
            "published": "04 Sep 2025 00:01:00",
        }

        with patch("resources.headlines.get_jina_reader_content") as mock_jina, patch(
            "resources.headlines.get_summary"
        ) as mock_summary:
            # Mock OpenAI response
            mock_summary.return_value = "Fallback summary for legal article"

            result = await process_entry(test_entry)

            # Should not call Jina Reader for problematic URLs
            assert mock_jina.call_count == 0
            
            # Should still return a valid result with fallback content
            assert result is not None
            assert result["title"] == "Test LawNet Article"
            assert "Content could not be retrieved" in result["text"]
            assert result["summary"] == "Fallback summary for legal article"

