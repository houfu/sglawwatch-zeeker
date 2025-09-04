"""
Headlines resource for fetching Singapore Law Watch Headlines RSS feed.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Optional

import click
import feedparser
import httpx
from sqlite_utils.db import Table
from tenacity import retry, stop_after_attempt, wait_exponential

HEADLINES_URL = "https://www.singaporelawwatch.sg/Portals/0/RSS/Headlines.xml"

SYSTEM_PROMPT_TEXT = """
As an expert in legal affairs, your task is to provide summaries of legal news articles for time-constrained attorneys in an engaging, conversational style. These summaries should highlight the critical legal aspects, relevant precedents, and implications of the issues discussed in the articles. The summary should be in 1 narrative paragraph and should not be longer than 100 words, but ensure they efficiently deliver the key legal insights, making them beneficial for quick comprehension. The end goal is to help the lawyers understand the crux of the articles without having to read them in their entirety.
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=1, max=10))
async def get_jina_reader_content(link: str) -> str:
    """Fetch content from the Jina reader link."""
    jina_token = os.environ.get("JINA_API_TOKEN")
    if not jina_token:
        click.echo("JINA_API_TOKEN environment variable not set", err=True)
        return ""
    jina_link = f"https://r.jina.ai/{link}"
    headers = {
        "Authorization": f"Bearer {jina_token}",
        "X-Retain-Images": "none",
        "X-Target-Selector": "article",
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.get(jina_link, headers=headers)
            r.raise_for_status()  # Raises httpx.HTTPStatusError for 4xx/5xx responses
        return r.text
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        click.echo(f"Error fetching content from Jina reader: {e}", err=True)
        raise


async def get_summary(text: str) -> str:
    """Generate a summary of the article text using OpenAI."""
    if not os.environ.get("OPENAI_API_KEY"):
        click.echo("OPENAI_API_KEY environment variable not set", err=True)
        return ""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(max_retries=3, timeout=60)
    try:
        response = await client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT_TEXT}]},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": f"Here is an article to summarise:\n {text}"}
                    ],
                },
            ],
            text={"format": {"type": "text"}},
            reasoning={"effort": "low", "summary": "auto"},
            store=False,
        )
        return response.output_text
    except Exception as e:
        click.echo(f"Error generating summary from OpenAI: {e}", err=True)
        raise


def get_hash_id(elements: list[str], delimiter: str = "|") -> str:
    """Generate a hash ID from a list of strings.

    Args:
        elements: List of strings to be hashed.
        delimiter: String used to join elements (default: "|").

    Returns:
        A hexadecimal MD5 hash of the joined elements.

    Examples:
        >>> get_hash_id(["2025-05-16", "Meeting Notes"])
        '1a2b3c4d5e6f7g8h9i0j'

        >>> get_hash_id(["user123", "login", "192.168.1.1"], delimiter=":")
        '7h8i9j0k1l2m3n4o5p6q'
    """
    import hashlib

    if not elements:
        raise ValueError("At least one element is required")

    joined_string = delimiter.join(str(element) for element in elements)
    return hashlib.md5(joined_string.encode()).hexdigest()


def convert_date_to_iso(date_str: str) -> str:
    """Convert date string like '08 May 2025 00:01:00' to ISO format."""
    try:
        parsed_date = datetime.strptime(date_str, "%d %B %Y %H:%M:%S")
        return parsed_date.isoformat()  # Returns '2025-05-08T00:01:00'
    except ValueError:
        # Handle potential parsing errors
        try:
            # Try alternative format with abbreviated month name
            parsed_date = datetime.strptime(date_str, "%d %b %Y %H:%M:%S")
            return parsed_date.isoformat()
        except ValueError:
            # If all parsing attempts fail, return original or a default
            return datetime.now().isoformat()


async def process_entry(entry: Dict) -> Optional[Dict]:
    """Process an entry from the RSS feed to extract necessary data."""
    try:
        # Convert ISO date string to datetime object
        entry_date = datetime.fromisoformat(convert_date_to_iso(entry["published"]))

        # Prepare entry data dictionary
        entry_data = {
            "id": entry.get("id", get_hash_id([entry_date.isoformat(), entry["title"]])),
            "category": entry.get("category", ""),
            "title": entry.get("title", ""),
            "source_link": entry.get("link", ""),
            "author": entry.get("author", ""),
            "date": entry_date.isoformat(),
            "imported_on": datetime.now().isoformat(),
        }

        # Fetch content from Jina reader with graceful fallback
        click.echo(f"Processing: {entry_data['title']} from {entry_data['date']}")
        
        # Check if URL is problematic (some URLs cause 422 errors with Jina Reader)
        source_url = entry_data["source_link"]
        skip_jina = any(pattern in source_url for pattern in [
            'store.lawnet.com',  # Known to cause 422 errors
            'utm_source=',       # URLs with tracking parameters sometimes fail
        ])
        
        try:
            if skip_jina:
                click.echo(f"  → Skipping Jina Reader for problematic URL pattern")
                raise Exception("URL pattern known to cause issues")
            entry_data["text"] = await get_jina_reader_content(source_url)
        except Exception as jina_error:
            click.echo(f"  → Jina Reader failed: {jina_error}", err=True)
            # Use fallback: title as content for summary generation
            entry_data["text"] = f"Article: {entry_data['title']}\nSource: {source_url}\n\nContent could not be retrieved from source."
            click.echo(f"  → Using fallback content for summary generation")

        # Generate summary using OpenAI
        click.echo(f"  → Generating summary for: {entry_data['title']}")
        try:
            entry_data["summary"] = await get_summary(entry_data["text"])
        except Exception as summary_error:
            click.echo(f"  → Summary generation failed: {summary_error}", err=True)
            # Fallback: use truncated title as summary
            entry_data["summary"] = f"Legal news article: {entry_data['title'][:100]}{'...' if len(entry_data['title']) > 100 else ''}"
            click.echo(f"  → Using fallback summary")

        return entry_data
    except Exception as e:
        click.echo(f"Error processing entry '{entry.get('title', 'Unknown')}': {e}", err=True)
        return None


def _get_existing_data(existing_table: Optional[Table]) -> tuple[set, Optional[datetime]]:
    """Extract existing IDs and last update time from table."""
    existing_ids = set()
    last_updated = None

    if not existing_table:
        return existing_ids, last_updated

    db = existing_table.db
    existing_ids = {row["id"] for row in existing_table.rows}

    if "_zeeker_updates" in db.table_names():
        updates_table = db["_zeeker_updates"]
        try:
            metadata = updates_table.get(existing_table.name)
            last_updated = datetime.fromisoformat(metadata["last_updated"])
        except Exception as e:
            print("No metadata found for this table yet:", str(e))

    return existing_ids, last_updated


def _should_skip_entry(
    entry: Dict,
    current_date: datetime,
    last_updated: Optional[datetime],
    existing_ids: set,
    max_day_limit: int = 60,
) -> tuple[bool, str]:
    """Check if entry should be skipped and return skip reason."""
    title = entry.get("title", "")

    if title.startswith("ADV:"):
        return True, "advertisement"

    try:
        entry_date = datetime.fromisoformat(convert_date_to_iso(entry.get("published", "")))
    except ValueError:
        click.echo(f"Error parsing date for entry: {title}", err=True)
        return True, "date_error"

    days_old = (current_date - entry_date).days
    if days_old > max_day_limit:
        return True, "too_old"

    if last_updated and entry_date <= last_updated:
        return True, "already_processed_by_time"

    entry_id = get_hash_id([entry_date.isoformat(), str(title)])
    if existing_ids and entry_id in existing_ids:
        return True, "already_processed_by_id"

    return False, ""


def _log_skip_counts(
    skipped_adv_count: int,
    skipped_old_count: int,
    skipped_processed_time_count: int,
    skipped_processed_id_count: int,
    max_day_limit: int,
):
    """Log summary of skipped entries."""
    if skipped_adv_count > 0:
        click.echo(f"Skipped {skipped_adv_count} advertisements")
    if skipped_old_count > 0:
        click.echo(f"Skipped {skipped_old_count} headlines older than {max_day_limit} days")
    if skipped_processed_time_count > 0:
        click.echo(
            f"Skipped {skipped_processed_time_count} headlines older than last update timestamp"
        )
    if skipped_processed_id_count > 0:
        click.echo(f"Skipped {skipped_processed_id_count} headlines with duplicate IDs in database")


async def fetch_data(existing_table: Optional[Table]):
    """
    Fetch data for the headlines table.

    Args:
        existing_table: sqlite-utils Table object if table exists, None for new table
                       Use this to check for existing data and avoid duplicates

    Returns:
        List[Dict[str, Any]]: List of records to insert into database

    """
    click.echo(f"Fetching headlines from {HEADLINES_URL}")
    feed = feedparser.parse(HEADLINES_URL)
    max_day_limit = 60
    current_date = datetime.now()

    existing_ids, last_updated = _get_existing_data(existing_table)

    tasks = []
    new_entries_count = 0
    skipped_adv_count = 0
    skipped_old_count = 0
    skipped_processed_time_count = 0
    skipped_processed_id_count = 0

    for entry in feed.entries:
        should_skip, skip_reason = _should_skip_entry(
            entry, current_date, last_updated, existing_ids, max_day_limit
        )

        if should_skip:
            title = entry.get("title", "")
            if skip_reason == "advertisement":
                skipped_adv_count += 1
                click.echo(f"Skipping advertisement: {title}")
            elif skip_reason == "too_old":
                skipped_old_count += 1
                days_old = (
                    current_date
                    - datetime.fromisoformat(convert_date_to_iso(entry.get("published", "")))
                ).days
                click.echo(f"Skipping old headline ({days_old} days): {title}")
            elif skip_reason == "already_processed_by_time":
                skipped_processed_time_count += 1
                entry_date_str = entry.get("published", "")
                click.echo(
                    f"  → Skipping (published {entry_date_str}, before last_updated {last_updated.strftime('%Y-%m-%d %H:%M:%S') if last_updated else 'None'}): {title}"
                )
            elif skip_reason == "already_processed_by_id":
                skipped_processed_id_count += 1
                click.echo(f"  → Skipping (duplicate ID in database): {title}")
            continue

        new_entries_count += 1
        task = asyncio.create_task(process_entry(entry))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    click.echo(f"Added {new_entries_count} new headlines")
    _log_skip_counts(
        skipped_adv_count,
        skipped_old_count,
        skipped_processed_time_count,
        skipped_processed_id_count,
        max_day_limit,
    )
    return results
