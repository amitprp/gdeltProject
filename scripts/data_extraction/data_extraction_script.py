import gdelt
from datetime import datetime
import re
import pandas as pd
import os
import json
from pymongo import MongoClient
from datetime import datetime, timedelta
from utlis import (
    extract_gdelt_data,
    refactor_data_df,
    create_mongo_docs,
    get_latest_event_time,
    insert_to_mongo,
    create_save_docs_event,
    extract_classified_articles,
)
from backend.app.core.database import db

def main():

    # # Get dates for the past year or from last extraction
    # end = datetime.now()
    # latest_event_time = get_latest_event_time(db)
    # start = latest_event_time if latest_event_time else datetime(2021, 1, 1)
    
    # Set specific dates for extraction
    start = datetime(2021, 1, 1)
    end = datetime(2021, 1, 31)

    print(f"Starting extraction from {start} to {end}")

    # Loop through each day
    current_date = start
    while current_date < end:
        start_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        next_date = current_date + timedelta(days=1)
        end_date = min(next_date, end).strftime("%Y-%m-%d %H:%M:%S")

        extract_classified_articles(start_date, end_date)

        current_date = next_date

if __name__ == "__main__":
    main()


# Overall Tone (first number): 2.25890529973936
# This is the main sentiment score
# Positive values indicate positive sentiment
# Negative values indicate negative sentiment
# The magnitude indicates the strength of the sentiment
# Positive Tone (second number): 4.77845351867941
# Measures the positive aspects of the text
# Higher values indicate more positive language
# Negative Tone (third number): 2.51954821894005
# Measures the negative aspects of the text
# Higher values indicate more negative language
# Polarity (fourth number): 7.29800173761946
# The difference between positive and negative tone
# Indicates how polarized the text is
# Activity (fifth number): 20.9383145091225
# Measures the level of activity or action in the text
# Higher values indicate more active/energetic language
# Emotionality (sixth number): 1.30321459600348
# Measures the emotional intensity of the text
# Higher values indicate more emotional language
# Word Count (seventh number): 1026
# The number of words analyzed in the text
