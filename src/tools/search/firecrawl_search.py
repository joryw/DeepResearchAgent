import os
import time

from dotenv import load_dotenv
load_dotenv(verbose=True)

from typing import List
from firecrawl import FirecrawlApp
import asyncio

from src.tools.search.base import WebSearchEngine, SearchItem

def search(params):
    """
    Perform a Google search using the provided parameters.
    Returns a list of SearchItem objects.
    """
    app = FirecrawlApp(
        api_key=os.getenv("FIRECRAWL_API_KEY"),
    )

    response = app.search(
        query=params["q"],
        limit=params.get("num", 10),
        # Firecrawl v2 expects None/omitted when no time filter; empty string is invalid
        tbs=(params.get("tbs") or None),
    )

    # Firecrawl v2 returns SearchData with fields like .web/.news/.images
    results = []
    sources = []
    # Collect available sources safely
    for source_name in ("web", "news", "images"):
        items = getattr(response, source_name, None)
        if items:
            sources.extend(items)

    for item in sources:
        # item may be a pydantic model with attributes or a dict
        title = (
            getattr(item, "title", None)
            or (item.get("title") if isinstance(item, dict) else None)
            or ""
        )
        url = (
            getattr(item, "url", None)
            or (item.get("url") if isinstance(item, dict) else None)
            or ""
        )
        description = (
            getattr(item, "description", None)
            or getattr(item, "snippet", None)
            or (item.get("description") if isinstance(item, dict) else None)
            or (item.get("snippet") if isinstance(item, dict) else None)
            or ""
        )
        results.append(SearchItem(title=title, url=url, description=description))

    return results

class FirecrawlSearchEngine(WebSearchEngine):
    async def perform_search(
        self,
        query: str,
        num_results: int = 10,
        filter_year: int = None,
        *args, **kwargs
    ) -> List[SearchItem]:
        """
        Google search engine.

        Returns results formatted according to SearchItem model.
        """
        params = {
            "q": query,
            "num": num_results,
        }
        if filter_year is not None:
            params["tbs"] = f"cdr:1,cd_min:01/01/{filter_year},cd_max:12/31/{filter_year}"
        else:
            params["tbs"] = None;

        results = search(params)

        return results


if __name__ == '__main__':
    # Example usage
    start_time = time.time()
    search_engine = FirecrawlSearchEngine()
    query = "OpenAI GPT-4"
    results = asyncio.run(search_engine.perform_search(query, num_results=5))

    for item in results:
        print(f"Title: {item.title}\nURL: {item.url}\nDescription: {item.description}\n")

    end_time = time.time()

    print(end_time - start_time, "seconds elapsed for search")