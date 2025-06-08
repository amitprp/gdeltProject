from datetime import datetime, timedelta
from scripts.data_extraction.utlis import extract_gdelt_data, get_latest_event_time
from backend.app.core.database import db
import threading
import time

class GdeltExtractionService:
    def __init__(self):
        self.latest_event_time = get_latest_event_time(db)
        # Run initial data extraction
        self._extract_data()
        # Start the periodic thread
        self.gdelt_extraction_thread = self._start_periodic_extraction()

    def _extract_data(self):
        end_date = datetime.now()
        if self.latest_event_time is None:
            start_date = end_date - timedelta(days=1)
        else:
            start_date = self.latest_event_time
        while start_date < end_date:
            extract_gdelt_data(start_date, end_date)
            start_date = start_date + timedelta(days=1)
        # Update the latest event time after extraction
        self.latest_event_time = end_date

    def _periodic_extraction(self):
        while True:
            # Sleep for 24 hours
            time.sleep(24 * 60 * 60)  # 24 hours in seconds
            self._extract_data()

    def _start_periodic_extraction(self):
        thread = threading.Thread(target=self._periodic_extraction)
        thread.daemon = True  # This ensures the thread will be terminated when the main program exits
        thread.start()
        return thread
            
