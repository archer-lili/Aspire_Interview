import os
import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Set up paths using os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
EMBEDDINGS_FILE = os.path.join(BASE_DIR, "media_embeddings.pkl")

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')


def load_media_data():
    """Load media data from JSON file."""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_or_generate_embeddings():
    """Load embeddings from pickle or generate and save them."""
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, 'rb') as f:
            data = pickle.load(f)
        return data

    print("Generating embeddings from data.json...")

    media_data = load_media_data()
    texts = [
        f"{item['title']} {item['creator']} {item['genre']} {item.get('description', '')}"
        for item in media_data
    ]
    titles = [item['title'] for item in media_data]
    embeddings = model.encode(texts, convert_to_tensor=True)

    data = {
        "titles": titles,
        "embeddings": embeddings
    }

    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(data, f)

    return data


def recommend_media(user_query, top_k=3, threshold=0.3):
    """Recommend media based on cosine similarity with user query."""
    data = load_or_generate_embeddings()
    query_embedding = model.encode(user_query, convert_to_tensor=True)

    scores = util.cos_sim(query_embedding, data['embeddings'])[0]
    scored_results = sorted(zip(data['titles'], scores), key=lambda x: x[1], reverse=True)

    recommendations = [
        (title, float(score))
        for title, score in scored_results
        if score >= threshold
    ][:top_k]

    if not recommendations:
        return ["I don't know. Consult the reception."]

    return [f"{title} (score: {score:.2f})" for title, score in recommendations]
