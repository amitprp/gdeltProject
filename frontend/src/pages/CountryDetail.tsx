import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getCountryData, getColorByValue, CountryData, getCountryTimeStats, CountryTimeStats } from '@/services/dataService';
import { AlertTriangle, Globe, Newspaper, Calendar, FileX } from 'lucide-react';
import { DatePicker } from "@/components/ui/date-picker";
import { ExportButton } from "@/components/ExportButton";
import BackToHome from "@/components/BackToHome";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const CountryDetail: React.FC = () => {
  const { iso2 = '' } = useParams<{ iso2: string }>();
  const navigate = useNavigate();
  const [country, setCountry] = useState<CountryData | null>(null);
  const [timeStats, setTimeStats] = useState<CountryTimeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();
  const [dateError, setDateError] = useState<string | null>(null);
  
  const chartRef = useRef<HTMLDivElement>(null);
  const articlesRef = useRef<HTMLDivElement>(null);

  // Date validation function
  const validateDates = (start: Date | undefined, end: Date | undefined): boolean => {
    setDateError(null);
    const now = new Date();

    if (start && end) {
      if (start > end) {
        setDateError("Start date must be before end date");
        return false;
      }
    }

    if (start && start > now) {
      setDateError("Start date cannot be in the future");
      return false;
    }

    if (end && end > now) {
      setDateError("End date cannot be in the future");
      return false;
    }

    return true;
  };

  // Handle date changes
  const handleStartDateChange = (date: Date | undefined) => {
    setStartDate(date);
    if (date && endDate) {
      validateDates(date, endDate);
    }
  };

  const handleEndDateChange = (date: Date | undefined) => {
    setEndDate(date);
    if (startDate && date) {
      validateDates(startDate, date);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // First try to get basic country info
        const countryData = await getCountryData(iso2);
        
        // If we get null or undefined for countryData, the country doesn't exist
        if (!countryData) {
          setError('Country not found');
          setLoading(false);
          return;
        }

        // We have valid country data, set it
        setCountry(countryData);

        // Now try to get the time stats
        if ((startDate || endDate) && !validateDates(startDate, endDate)) {
          return;
        }

        try {
          const timeStatsData = await getCountryTimeStats(iso2, startDate, endDate);
          setTimeStats(timeStatsData);
        } catch (timeStatsError) {
          // If we fail to get time stats, just set empty stats
          // This is not an error state, just means no articles
          setTimeStats({
            articleCount: 0,
            averageTone: 0,
            timelineData: [],
            articles: []
          });
        }
      } catch (error) {
        // Only set error if it's specifically about country not found
        if (error instanceof Error && error.message.includes('not found')) {
          setError('Country not found');
        } else {
          // For other errors, we'll still try to show the country page
          console.error("Error fetching data:", error);
          setTimeStats({
            articleCount: 0,
            averageTone: 0,
            timelineData: [],
            articles: []
          });
        }
      } finally {
        setLoading(false);
      }
    };

    if (iso2) {
      fetchData();
    }
  }, [iso2, startDate, endDate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-lg">Loading country data...</p>
        </div>
      </div>
    );
  }

  // Only show the error page if we explicitly got a "country not found" error
  if (error === 'Country not found') {
    return (
      <div className="container mx-auto py-8 px-4">
        <BackToHome />
        <div className="text-center py-16">
          <AlertTriangle className="h-16 w-16 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Country Not Found</h2>
          <p className="text-muted-foreground mb-6">
            We couldn't find the requested country.
          </p>
          <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
        </div>
      </div>
    );
  }

  // If we have country data, show the page regardless of whether we have articles
  if (country) {
    const hasArticles = timeStats && timeStats.articleCount > 0;

    const getSeverityLabel = (value: number) => {
      if (value === 0) return "Low";
      if (value < 100) return "Low";
      if (value < 200) return "Medium";
      if (value < 300) return "High";
      return "Severe";
    };

    const getSeverityColor = (value: number) => {
      if (value === 0) return "bg-map-low";
      const colorClass = getColorByValue(value);
      return `bg-${colorClass}`;
    };

    const getProgressValue = (value: number) => {
      return Math.min(100, (value / 5));
    };

    return (
      <div className="container mx-auto py-8 px-4">
        <BackToHome />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-3 shadow-md">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-2xl md:text-3xl flex items-center">
                  <Globe className="mr-3 h-6 w-6" />
                  {country.name}
                </CardTitle>
                {hasArticles && (
                  <div className="flex items-center gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Start Date</label>
                      <DatePicker date={startDate} setDate={handleStartDateChange} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">End Date</label>
                      <DatePicker date={endDate} setDate={handleEndDateChange} />
                    </div>
                  </div>
                )}
              </div>
              {dateError && (
                <div className="mt-2 text-sm text-destructive">
                  {dateError}
                </div>
              )}
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row items-center justify-between">
                <div className="mb-4 md:mb-0">
                  <div className="text-sm text-muted-foreground mb-1">Antisemitism Level</div>
                  <div className="text-3xl font-bold flex items-center">
                    {(!timeStats || timeStats.articleCount === 0) ? "Low" : getSeverityLabel(timeStats.articleCount)}
                    <span className={`ml-2 inline-block w-3 h-3 rounded-full ${(!timeStats || timeStats.articleCount === 0) ? 'bg-map-low' : getSeverityColor(timeStats.articleCount)}`}></span>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Articles in Period</div>
                  <div className="text-3xl font-bold">{timeStats?.articleCount.toLocaleString() || '0'}</div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm text-muted-foreground mb-1">Average Tone</div>
                  <div className="text-xl font-bold">{timeStats?.averageTone.toFixed(2) || '0.00'}</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {(!timeStats || timeStats.articleCount === 0) ? (
            <Card className="lg:col-span-3 shadow-md">
              <CardContent>
                <div className="text-center py-12">
                  <FileX className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Articles Found</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    No antisemitic articles have been detected for {country.name}.
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              <Card className="lg:col-span-2 shadow-md">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-xl">Article Frequency Over Time</CardTitle>
                  <ExportButton
                    targetRef={chartRef}
                    type="chart"
                    filename={`${country.name}-article-frequency`}
                  />
                </CardHeader>
                <CardContent>
                  <div className="h-[300px]" ref={chartRef}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={timeStats.timelineData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="count"
                          stroke="#2563eb"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="shadow-md">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-xl flex items-center">
                    <Newspaper className="mr-2 h-5 w-5" />
                    Recent Articles
                  </CardTitle>
                  <ExportButton
                    targetRef={articlesRef}
                    type="table"
                    data={timeStats.articles}
                    filename={`${country.name}-articles`}
                  />
                </CardHeader>
                <CardContent>
                  <div className="space-y-4" ref={articlesRef}>
                    {timeStats.articles.map((article, index) => (
                      <div key={index} className="rounded-md border p-3">
                        <h4 className="font-medium text-sm">{article.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1">
                          {article.date} - {article.source}
                        </p>
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline mt-1 block"
                        >
                          Read More →
                        </a>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    );
  }

  return null; // Fallback return
};

export default CountryDetail;

