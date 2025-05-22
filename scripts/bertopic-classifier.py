# E5 instruct - vector embedding model

import json
from pymongo import MongoClient
import pandas as pd
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from data.mapping_data.classification_data import against_israel_themes, against_israel_keywords

print("[INFO] Connecting to MongoDB and extracting articles...")
# --- MongoDB Extraction ---
client = MongoClient("mongodb://localhost:27017/")
db = client["JewWatch"]
collection = db["articles"]
all_docs = list(collection.find())
for doc in all_docs:
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])

print(f"[INFO] Extracted {len(all_docs)} articles from MongoDB.")

print("[INFO] Preprocessing articles (themes, tones, labels)...")


# --- Helper Functions ---
def extract_themes(theme_str):
    """Extract and clean themes from the theme string."""
    if not theme_str:
        return ""
    themes = [theme.split(",")[0] for theme in theme_str.split(";") if theme]
    return " ".join(dict.fromkeys(themes))


def extract_tones(tones):
    """Convert tones dict to a string representation for clustering."""
    if not tones or not isinstance(tones, dict):
        return ""
    return " ".join([f"{k}:{v}" for k, v in tones.items()])


def is_against_israel(doc):
    """Determine if an article is against Israel based on themes and keywords."""
    # Check themes
    if "themes" in doc:
        themes = extract_themes(doc["themes"])
        if any(theme in themes for theme in against_israel_themes):
            return True
    # Check keywords in title and content
    text = f"{doc.get('pageTitle', '')} {doc.get('content', '')}"
    if any(keyword in text.lower() for keyword in against_israel_keywords):
        return True
    return False


texts = []
labels = []
for doc in all_docs:
    text_parts = [
        doc.get("pageTitle", ""),
        extract_themes(doc.get("themes", "")),
        extract_tones(doc.get("tones", {})),
        doc.get("content", ""),
    ]
    text = " ".join([part for part in text_parts if part]).strip()
    texts.append(text)
    labels.append(is_against_israel(doc))

print(f"[INFO] Preprocessed {len(texts)} articles.")

print("[INFO] Fitting BERTopic model...")
# --- BERTopic Clustering ---
topic_model = BERTopic(min_topic_size=20, n_gram_range=(1, 2), verbose=True)
# Fit the model and get topics/probabilities
topics, probs = topic_model.fit_transform(texts)
print("[INFO] BERTopic model fitted.")

print("[INFO] Creating DataFrame and saving document-topic mapping...")
# Create DataFrame with results
if "doc_topics" not in locals():
    doc_topics = pd.DataFrame({"text": texts, "topic": topics, "isAgainstIsrael": labels})
doc_topics.to_csv("document_topics.csv", index=False)
print("[INFO] Document-topic mapping saved to document_topics.csv.")

print("[INFO] Generating and saving embeddings for 'against Israel' articles...")
# --- Embedding Model for Against Israel Articles ---
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
against_israel_texts = doc_topics[doc_topics["isAgainstIsrael"]]["text"].tolist()
against_israel_embeddings = embedding_model.encode(against_israel_texts)
np.save("against_israel_embeddings.npy", against_israel_embeddings)
embedding_model.save("embedding_model")
print("[INFO] Embeddings and model saved.")

# --- Debugging & Inspection Section ---
print("\n--- BERTopic Debugging & Inspection ---")

# Print topic info summary
topic_info = topic_model.get_topic_info()
print("\nTopic Info (first 5 rows):")
print(topic_info.head())

# Print topic frequencies (topic_info already includes frequency)
print("\nTopic Frequencies (from topic_info):")
print(topic_info[["Topic", "Count"]].head())

# Print all topics (first 2 topics)
print("\nTopics (first 2):")
topics_dict = topic_model.get_topics()
for topic_num in list(topics_dict.keys())[:2]:
    try:
        print(f"Topic {topic_num}: {topic_model.get_topic(int(topic_num))}\n")
    except Exception as e:
        print(f"Error printing topic {topic_num}: {e}")

# Print document info (first 5 docs)
doc_info = topic_model.get_document_info(texts)
print("\nDocument Info (first 5 rows):")
print(doc_info.head())

# Print representative docs for first 2 topics
print("\nRepresentative Docs for first 2 topics:")
rep_docs = topic_model.get_representative_docs()
if isinstance(rep_docs, dict):
    for topic_num in list(rep_docs.keys())[:2]:
        print(f"Topic {topic_num} representative docs:")
        for doc in rep_docs[topic_num][:2]:
            print(f"- {doc[:200]}...")
elif isinstance(rep_docs, list):
    for i, doc in enumerate(rep_docs[:2]):
        print(f"Representative doc {i}: {doc[:200]}...")

# Print some key attributes
print("\nKey BERTopic Attributes:")
if hasattr(topic_model, "topics_") and topic_model.topics_ is not None:
    print(f"topics_ (first 10): {topic_model.topics_[:10]}")
else:
    print("topics_ attribute not available.")
if hasattr(topic_model, "probabilities_") and topic_model.probabilities_ is not None:
    print(f"probabilities_ (shape): {np.array(topic_model.probabilities_).shape}")
print(f"topic_labels_ (first 5): {getattr(topic_model, 'topic_labels_', 'N/A')[:5]}")

print("\n--- End of BERTopic Debugging ---\n")
