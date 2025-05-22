export interface TimeFrameData {
  startDate: Date;
  endDate: Date;
  articleCount: number;
  dailyData: Array<{
    date: string;
    articleCount: number;
    averageTone: number;
  }>;
}

export const timeFrameComparison = async (
  timeFrame1Start: Date,
  timeFrame1End: Date,
  timeFrame2Start: Date,
  timeFrame2End: Date
): Promise<[TimeFrameData, TimeFrameData]> => {
  try {
    // Ensure all dates are sent with timezone information
    const formatDateWithTimezone = (date: Date) => {
      // If the date doesn't have timezone info, treat it as UTC
      if (!date.getTimezoneOffset()) {
        return date.toISOString();
      }
      // Convert to UTC if it has a timezone offset
      const utcDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
      return utcDate.toISOString();
    };

    const response = await fetch('/api/v1/articles/compare-trends', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        timeframe1_start: formatDateWithTimezone(timeFrame1Start),
        timeframe1_end: formatDateWithTimezone(timeFrame1End),
        timeframe2_start: formatDateWithTimezone(timeFrame2Start),
        timeframe2_end: formatDateWithTimezone(timeFrame2End)
      })
    });

    if (!response.ok) {
      throw new Error('Failed to fetch comparison data');
    }

    const data = await response.json();

    // Convert string dates back to Date objects
    const [timeFrame1, timeFrame2] = data;
    return [
      {
        ...timeFrame1,
        startDate: new Date(timeFrame1.startDate),
        endDate: new Date(timeFrame1.endDate)
      },
      {
        ...timeFrame2,
        startDate: new Date(timeFrame2.startDate),
        endDate: new Date(timeFrame2.endDate)
      }
    ];
  } catch (error) {
    console.error('Error comparing time frames:', error);
    throw error;
  }
}; 