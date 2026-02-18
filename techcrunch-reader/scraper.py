import os
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_article_urls():
    """Get article URLs from TechCrunch homepage"""
    url = "https://techcrunch.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)

    # Find all article URLs
    pattern = r'href="(https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[^"]+)"'
    urls = re.findall(pattern, response.text)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    return unique_urls[:10]  # Get first 10 unique articles

def scrape_article(url):
    """Scrape details from a single article page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Title
        title = ''
        title_el = soup.select_one('h1')
        if title_el:
            title = title_el.get_text(strip=True)

        # Author
        author = 'TechCrunch'
        author_el = soup.select_one('a[rel="author"], .article-hero__author-link, [class*="author"]')
        if author_el:
            author = author_el.get_text(strip=True)

        # Date
        date = ''
        time_el = soup.select_one('time[datetime]')
        if time_el:
            date = time_el.get('datetime', '')

        # Image - try multiple sources
        image = ''
        # Try og:image first (most reliable)
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            image = og_image.get('content', '')
        # Fallback to article image
        if not image:
            img_el = soup.select_one('article img, .article-hero img, figure img')
            if img_el:
                image = img_el.get('src') or img_el.get('data-src') or ''

        # Category
        category = ''
        cat_el = soup.select_one('a[class*="category"], .article-hero__category')
        if cat_el:
            category = cat_el.get_text(strip=True)

        # Content - get article paragraphs (preserve paragraph breaks)
        content = ''
        content_el = soup.select_one('.entry-content, .article-content, article')
        if content_el:
            paragraphs = content_el.select('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Tags
        tags = []
        tag_els = soup.select('a[href*="/tag/"], .tag-cloud a')
        for tag in tag_els[:5]:
            tag_text = tag.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        return {
            'title': title,
            'link': url,
            'author': author,
            'date': date,
            'image': image,
            'category': category,
            'content': content[:2000] if content else '',  # Limit to 2000 chars
            'excerpt': content[:300] if content else '',
            'tags': tags
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def main():
    print("Scraping TechCrunch...")

    # Get article URLs
    urls = get_article_urls()
    print(f"Found {len(urls)} article URLs")

    # Scrape each article
    articles = []
    for i, url in enumerate(urls):
        print(f"Scraping article {i+1}/{len(urls)}: {url[:60]}...")
        article = scrape_article(url)
        if article and article['title']:
            articles.append(article)

    # Save to JSON
    data = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'articles': articles
    }

    with open(os.path.join(SCRIPT_DIR, 'articles.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(articles)} articles to articles.json")

if __name__ == '__main__':
    main()
