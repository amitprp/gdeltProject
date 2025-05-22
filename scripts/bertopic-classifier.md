# BERTopic Classifier Script Documentation

## Purpose
This script extracts articles from a MongoDB collection, clusters them using BERTopic, and labels them as "against Israel" or not based on custom logic. It also generates embeddings for further analysis.

## Main Steps
1. **Extract Articles:**
   - Connects to the `JewWatch` MongoDB database and retrieves all documents from the `articles` collection.
2. **Preprocess Data:**
   - For each article, builds a text string from the title, themes, tones, and content (URL is excluded from clustering).
   - Computes a label (`isAgainstIsrael`) using a set of themes and keywords.
3. **Clustering:**
   - Uses BERTopic to cluster articles based on the combined text features (title, themes, tones, content).
   - The number of topics is determined by the model, not by the label.
4. **Output:**
   - Saves a CSV file (`document_topics.csv`) mapping each article to its topic and label.
   - Generates and saves sentence embeddings for articles labeled as "against Israel" (`against_israel_embeddings.npy`).
   - Saves the embedding model for future use (`embedding_model`).

## Features Used for Clustering
- **Title:** The article's title.
- **Themes:** Cleaned and deduplicated themes from the article.
- **Tones:** All tone values, converted to a string.
- **Content:** The main content of the article (if available).
- **URL:** Not used for clustering.

## Labeling Logic
- An article is labeled as `isAgainstIsrael=True` if:
  - Its themes match any in a predefined list (`against_israel_themes`), or
  - Its title or content contains any of the `against_israel_keywords`.

## Output Files
- `document_topics.csv`: CSV with text, topic, and label for each article.
- `against_israel_embeddings.npy`: Numpy array of embeddings for "against Israel" articles.
- `embedding_model`: Directory containing the saved sentence transformer model.

## Usage
1. Ensure MongoDB is running and contains the `JewWatch.articles` collection.
2. Place the required mapping lists in `data/mapping_data/mapping_lists.py`.
3. Run the script from the project root:
   ```sh
   python scripts/bertopic-classifier.py
   ```
4. Check the output files in the working directory.

## Requirements
- Python 3.7+
- pymongo
- bertopic
- sentence-transformers
- pandas
- numpy

## Notes
- The script is designed to be extensible for other types of content or labeling logic.
- The number of topics is determined by BERTopic based on the data, not forced to 2. 