import pickle
import threading
import time
from flask import Flask, render_template, request, session, redirect, url_for
from fetch_articles import fetch_and_store_articles

app = Flask(__name__)
app.secret_key = 'secret'

PICKLE_FILE = "articles.pkl"

def background_fetch():
    """Background thread to fetch articles every 15 minutes."""
    while True:
        print("Fetching new articles...")
        try:
            fetch_and_store_articles()
        except Exception as e:
            print(f"Error fetching articles: {e}")
        time.sleep(900)  # Sleep for 15 minutes

# Start background thread
fetch_thread = threading.Thread(target=background_fetch, daemon=True)
fetch_thread.start()


RSS_ARR = ['Yahoo Finance', 'Wall Street Journal', 'CNBC', 'Fox News - Business', 'Financial Times - Markets', 'Bloomberg - Markets', 'Reuters - Business', 'Forbes - Business', 'Fox News - Politics', 'Bloomberg - Politics', 'Politico - Politics', 'The Hill', 'NPR - Politics', 'New York Times - Technology', 'Wired', 'The Verge', 'CNET', 'BBC - World', 'The Guardian - World', 'Al Jazeera - Top Stories', 'Reuters - World News', 'CNN - World', 'NPR - World', 'NPR - News', 'Washington Post - Opinions', 'USA Today - News', 'ABC News - Top Stories']

# Bias Mapping
SOURCE_BIAS = {
    'Wall Street Journal': 'Right',
    'Fox News - Business': 'Right',
    'Fox News - Politics': 'Right',
    'The Hill': 'Right',
    'Forbes - Business': 'Right',
    'New York Times - Technology': 'Left',
    'Washington Post - Opinions': 'Left',
    'The Guardian - World': 'Left',
    'NPR - Politics': 'Left',
    'NPR - World': 'Left',
    'NPR - News': 'Left',
    'CNN - World': 'Left',
    'Politico - Politics': 'Left',
    'The Verge': 'Left',
    'Wired': 'Left',
    'BBC - World': 'Center',
    'Al Jazeera - Top Stories': 'Center',
    'Reuters - World News': 'Center',
    'Reuters - Business': 'Center',
    'USA Today - News': 'Center',
    'ABC News - Top Stories': 'Center',
    'CNBC': 'Center',
    'Yahoo Finance': 'Center',
    'Bloomberg - Markets': 'Center',
    'Bloomberg - Politics': 'Center',
    'Financial Times - Markets': 'Center',
    'CNET': 'Center'
}

def load_articles():
    try:
        with open(PICKLE_FILE, "rb") as f:
            articles = pickle.load(f)
    except FileNotFoundError:
        articles = []
    return articles


@app.route('/')
def index():
    articles = [i for i in load_articles() if i[0] in session.get('sources', RSS_ARR)]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    return render_template('index.html', articles=paginated_articles, page=page,
                           total_pages=(total_articles // per_page) + 1, sources=RSS_ARR, 
                           allowed=session.get('sources', RSS_ARR), source_bias=SOURCE_BIAS)

@app.route('/choose', methods=['POST'])
def choose():
    if request.method == 'POST':
        session['sources'] = request.form.getlist('sources') if request.form.getlist('sources') else RSS_ARR
        return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q')
    articles = load_articles()

    results = [article for article in articles if query.lower() in article[1].title.lower()]

    return render_template('search_results.html', articles=results, query=query, source_bias=SOURCE_BIAS)


if __name__ == '__main__':
    app.run(debug=True)
