import gdelt

TONE_WEIGHTS = {
    "overall": 2.0,  # Overall tone — neutral/mixed vs clear sentiment
    "positive": -1.0,  # Positive tones reduce suspicion of anti-Israel bias
    "negative": 2.0,  # Negative tones increase suspicion
    "polarity": 1.0,  # Polarity only strongly indicates bias when combined with negative tone
    "emotionality": 0.5,  # Emotional language may indicate bias
    "activity": 0.2,  # Less important, but included to reflect energy in the language
}

ARTICLES_COLLECTION="new_articles"
EVENTS_COLLECTION="new_events"

THEME_WEIGHT = 1.0  # Weight per matching theme
KEYWORD_WEIGHT = 2.0  # Weight per matching keyword
CLASSIFICATION_THRESHOLD = 7.0  # Final score threshold for classifying as 'against Israel'

gd = gdelt.gdelt(version=2)

# Function to load URL to country mapping
def load_url_to_country_mapping(file_path):
    url_to_country = {}
    country_code_to_name = {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    domain = parts[0].strip()
                    country_code = parts[1].strip()
                    country_name = parts[2].strip()

                    url_to_country[domain] = country_code
                    country_code_to_name[country_code] = country_name

    except Exception as e:
        print(f"Error loading URL to country mapping: {e}")

    return url_to_country, country_code_to_name

URL_TO_COUNTRY_MAPPING_PATH = "data/mapping_data/url-to-country-mapping.txt"
url_to_country, _ = load_url_to_country_mapping(URL_TO_COUNTRY_MAPPING_PATH)