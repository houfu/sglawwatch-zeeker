"""Tests for the commentaries resource."""

import asyncio

import resources.commentaries as commentaries_module
from resources.commentaries import _get_docling_semaphore


class TestSemaphoreLoopBinding:
    """Regression: docling Semaphore must rebind when asyncio.run is called more than once per process.

    Same failure mode as headlines._LLM_SEMAPHORE — the lazy-init guard
    (`if _docling_semaphore is None`) only protected against a *first* call
    in a fresh process. A second asyncio.run reused the stale Semaphore from
    the first loop and raised "bound to a different event loop".
    """

    def setup_method(self):
        commentaries_module._docling_semaphore = None
        commentaries_module._docling_semaphore_loop = None

    def test_get_docling_semaphore_rebinds_across_asyncio_run(self):
        async def acquire_release():
            sem = _get_docling_semaphore()
            async with sem:
                pass
            return sem

        sem1 = asyncio.run(acquire_release())
        sem2 = asyncio.run(acquire_release())

        assert sem1 is not sem2

    def test_get_docling_semaphore_stable_within_one_run(self):
        async def two_acquires():
            return _get_docling_semaphore(), _get_docling_semaphore()

        a, b = asyncio.run(two_acquires())
        assert a is b
