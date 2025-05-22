from datetime import datetime, timezone
from typing import Optional, Tuple

def validate_date_range(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    allow_future: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validates a date range to ensure:
    1. If both dates are provided, start_date is before end_date
    2. Dates are not in the future (unless allow_future is True)
    3. Dates are timezone-aware (converts naive dates to UTC)
    
    Returns:
    - tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    current_time = datetime.now(timezone.utc)
    
    # Convert naive datetimes to UTC
    if start_date and start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date and end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
        
    if start_date and end_date and start_date > end_date:
        return False, "Start date must be before end date"
        
    if not allow_future:
        if start_date and start_date > current_time:
            return False, "Start date cannot be in the future"
        if end_date and end_date > current_time:
            return False, "End date cannot be in the future"
            
    return True, None 