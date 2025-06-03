import gdelt
from datetime import datetime, timedelta
from pymongo import MongoClient
from data_extraction_script import (
    load_url_to_country_mapping,
    extract_gdelt_data,
    refactor_data_df,
    create_mongo_docs,
    get_latest_event_time,
)
from classify_and_upsert_articles import run_classification

def main():
    try:
        # Initialize MongoDB connection
        client = MongoClient("mongodb://localhost:27017/")
        db = client["JewWatch"]
        print("[INFO] Successfully connected to MongoDB")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        db = ""

    # Initialize GDELT
    gd = gdelt.gdelt(version=2)
    print("[INFO] GDELT initialized")

    # Load URL to country mapping
    url_to_country, country_code_to_name = load_url_to_country_mapping("url-to-country-mapping.txt")
    print(f"[INFO] Loaded {len(url_to_country)} URL to country mappings")

    # Get dates for extraction
    end = datetime.now()
    latest_event_time = get_latest_event_time(db)
    start = latest_event_time if latest_event_time else (end - timedelta(days=365))

    print(f"[INFO] Starting extraction from {start} to {end}")

    # Process data day by day
    current_date = start
    total_articles = 0
    while current_date < end:
        start_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        next_date = current_date + timedelta(days=1)
        end_date = min(next_date, end).strftime("%Y-%m-%d %H:%M:%S")

        print(f"[INFO] Processing data from {start_date} to {end_date}")

        try:
            # Extract data from GDELT
            results = extract_gdelt_data(gd, start_date, end_date)
            result_df = refactor_data_df(results, url_to_country)
            print(f"[INFO] Found {len(result_df)} matching articles")

            if len(result_df) > 0:
                # Create MongoDB documents
                mongo_docs = create_mongo_docs(result_df)
                
                # Insert into MongoDB
                if db:
                    collection = db["articles"]
                    collection.insert_many(mongo_docs)
                    print(f"[INFO] Inserted {len(mongo_docs)} documents into MongoDB")
                    total_articles += len(mongo_docs)
                else:
                    print("[WARNING] No MongoDB connection, skipping insertion")

        except Exception as e:
            print(f"[ERROR] Failed processing data for {start_date}: {str(e)}")

        current_date = next_date

    print(f"[INFO] Completed data extraction. Total articles extracted: {total_articles}")

    # Run classification on all articles
    if db:
        print("[INFO] Starting article classification...")
        run_classification()
        print("[INFO] Completed article classification")
    else:
        print("[WARNING] Skipping classification due to no MongoDB connection")

if __name__ == "__main__":
    main() 