import pickle
import threading
import time
import os
from flask import Flask, render_template, request, session, redirect, url_for
from fetch_articles import fetch_and_store_articles
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
import numpy as np

app = Flask(__name__)
app.secret_key = 'secret'

PICKLE_FILE = "articles.pkl"
MODEL_PATH = os.path.join('models', 'classifiers', 'random_forest_model.pkl')

# Prediction pipeline globals
RF_MODEL = None
VECT = None
SVD = None
SCALER = None
PIPELINE_READY = False

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


def _extract_text_from_obj(obj):
    if obj is None:
        return ""
    if isinstance(obj, dict):
        for key in ('title', 'summary', 'description', 'content'):
            if key in obj and obj[key]:
                return str(obj[key])
        return str(obj)
    for attr in ('title', 'summary', 'description', 'content'):
        if hasattr(obj, attr) and getattr(obj, attr):
            return str(getattr(obj, attr))
    return str(obj)


def init_prediction_pipeline():
    global RF_MODEL, VECT, SVD, SCALER, PIPELINE_READY
    try:
        RF_MODEL = joblib.load(MODEL_PATH)
    except Exception:
        RF_MODEL = None
        PIPELINE_READY = False
        return

    articles = load_articles()
    texts = []
    for a in articles:
        try:
            texts.append(_extract_text_from_obj(a[1]))
        except Exception:
            texts.append("")

    if not texts:
        PIPELINE_READY = False
        return

    try:
        VECT = TfidfVectorizer(max_features=10, ngram_range=(1,2), stop_words='english')
        X_tfidf = VECT.fit_transform(texts)
        n_comp = max(1, min(10, X_tfidf.shape[1] - 1))
        SVD = TruncatedSVD(n_components=n_comp, random_state=42)
        X_reduced = SVD.fit_transform(X_tfidf)
        SCALER = StandardScaler()
        SCALER.fit(X_reduced)
        PIPELINE_READY = True
    except Exception:
        PIPELINE_READY = False


# Initialize pipeline at startup
init_prediction_pipeline()


@app.route('/')
def index():
    articles = [i for i in load_articles() if i[0] in session.get('sources', RSS_ARR)]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    augmented = []
    if PIPELINE_READY and RF_MODEL is not None:
        texts = [_extract_text_from_obj(a[1]) for a in paginated_articles]
        try:
            X_tfidf = VECT.transform(texts)
            X_red = SVD.transform(X_tfidf)
            X_scaled = SCALER.transform(X_red)
            probs = RF_MODEL.predict_proba(X_scaled)[:, 1]
            for a, p in zip(paginated_articles, probs):
                augmented.append((a[0], a[1], f"{int(round(p*100))}%", p))
        except Exception:
            for a in paginated_articles:
                augmented.append((a[0], a[1], "N/A", 0.0))
    else:
        for a in paginated_articles:
            augmented.append((a[0], a[1], "N/A", 0.0))

    return render_template('index.html', articles=augmented, page=page,
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

    augmented = []
    if PIPELINE_READY and RF_MODEL is not None and results:
        texts = [_extract_text_from_obj(a[1]) for a in results]
        try:
            X_tfidf = VECT.transform(texts)
            X_red = SVD.transform(X_tfidf)
            X_scaled = SCALER.transform(X_red)
            probs = RF_MODEL.predict_proba(X_scaled)[:, 1]
            for a, p in zip(results, probs):
                augmented.append((a[0], a[1], f"{int(round(p*100))}%", p))
        except Exception:
            for a in results:
                augmented.append((a[0], a[1], "N/A", 0.0))
    else:
        for a in results:
            augmented.append((a[0], a[1], "N/A", 0.0))

    return render_template('search_results.html', articles=augmented, query=query, source_bias=SOURCE_BIAS)


if __name__ == '__main__':
    app.run(debug=True)
