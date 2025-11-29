import feedparser
import pickle, time
from datetime import datetime
import ssl

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

RSS_FEEDS = {
    'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex',
    'Wall Street Journal': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
    'CNBC': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069',
    'Fox News - Business': 'https://feeds.foxnews.com/foxnews/business',
    'Financial Times - Markets': 'https://www.ft.com/markets?format=rss',
    'Bloomberg - Markets': 'https://www.bloomberg.com/markets/feeds/site.xml',
    'Reuters - Business': 'https://www.reuters.com/business/rssFeed',
    'Forbes - Business': 'https://www.forbes.com/business/feed/',
    
    'Fox News - Politics': 'https://feeds.foxnews.com/foxnews/politics',
    'Bloomberg - Politics': 'https://www.bloomberg.com/politics/feeds/site.xml',
    'Politico - Politics': 'https://www.politico.com/rss/politics.xml',
    'The Hill': 'https://thehill.com/rss/syndicator/19110',
    'NPR - Politics': 'https://feeds.npr.org/1014/rss.xml',

    'New York Times - Technology': 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
    'Wired': 'https://www.wired.com/feed/rss',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    'CNET': 'https://www.cnet.com/rss/news/',


    'BBC - World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'The Guardian - World': 'https://www.theguardian.com/world/rss',
    'Al Jazeera - Top Stories': 'https://www.aljazeera.com/xml/rss/all.xml',
    'Reuters - World News': 'https://www.reuters.com/world/rssFeed',
    'CNN - World': 'http://rss.cnn.com/rss/edition_world.rss',
    'NPR - World': 'https://feeds.npr.org/1004/rss.xml',
    

    'NPR - News': 'https://feeds.npr.org/1001/rss.xml',
    'Washington Post - Opinions': 'https://feeds.washingtonpost.com/rss/opinions',
    'USA Today - News': 'http://rssfeeds.usatoday.com/usatoday-NewsTopStories',
    'ABC News - Top Stories': 'https://abcnews.go.com/abcnews/topstories',
}

PICKLE_FILE = "articles.pkl"


def fetch_and_store_articles():
    articles = []
    
    today = datetime.now().date()
    
    feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    for source, feed in RSS_FEEDS.items():
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                entry_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).date()
                
                if (today - entry_date).days <= 1:
                    articles.append((source, entry))
    
    print(f"Saved {len(articles)} articles to {PICKLE_FILE}")
    
    articles = sorted(articles, key=lambda x: x[1].published_parsed if hasattr(x[1], 'published_parsed') else time.struct_time((2000, 1, 1, 0, 0, 0, 0, 1, -1)), reverse=True)

    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(articles, f)

    print(f"Saved {len(articles)} articles to {PICKLE_FILE}")


if __name__ == '__main__':
    fetch_and_store_articles()
