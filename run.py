import asyncio
import aiohttp
import csv
from urllib.parse import urlparse, urljoin
import re

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            content_type = response.headers.get('Content-Type', 'unknown')
            if any(ct in content_type for ct in ['text/html', 'application/pdf', 'audio/mpeg', 'video/mp4']):
                return url, response.status, content_type
            else:
                return None  # Return None if the content type is not one of the specified types
    except Exception as e:
        return url, str(e), 'unknown'



async def get_links(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    text = await response.text()
                    links = re.findall(r'href=["\'](https?://.*?)(?=["\'])', text)
                    # Resolve relative links
                    resolved_links = [urljoin(url, link) for link in links]
                    return [link for link in resolved_links if urlparse(link).netloc == urlparse(url).netloc]
            return []  # Return an empty list if the content type is not HTML or if there's an error
    except Exception:
        return []  # Return an empty list in case of any exception

async def crawl(domain, url, visited, results, session):
    print(f"Attempting to crawl: {url}")
    if url in visited:
        print(f"Already visited: {url}")
        return
    visited.add(url)

    result = await fetch(session, url)
    if result:
        results.append(result)
        print(f"Crawled: {url} - Status: {result[1]} - Content Type: {result[2]}")

    links = await get_links(session, url)
    print(f"Links found: {links}")
    if links is not None:
        for link in links:
            print(f"Crawling link: {link}")
            await crawl(domain, link, visited, results, session)


async def main(start_url):
    domain = urlparse(start_url).netloc
    visited = set()
    results = []

    async with aiohttp.ClientSession() as session:
        await crawl(domain, start_url, visited, results, session)

    # Sort results alphabetically by URL
    results.sort(key=lambda x: x[0])

    # Write results to CSV
    with open('crawled_links.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'HTTP Status', 'Content Type'])
        for url, status, content_type in results:
            writer.writerow([url, status, content_type])


if __name__ == "__main__":
    start_url = input("Enter the URL to start crawling: ")
    asyncio.run(main(start_url))
