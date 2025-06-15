import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getCountryData, getColorByValue, CountryData, getCountryTimeStats } from '@/services/dataService';
import { AlertTriangle, Globe, Newspaper, Calendar, FileX, ChevronLeft, ChevronRight } from 'lucide-react';
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
  ResponsiveContainer,
  Legend,
  ReferenceArea,
  ReferenceLine,
  Brush
} from 'recharts';

// Add interface for raw timeline data item from API
interface RawTimelineItem {
  date: string;
  count: number;
  tone: number;  // This comes from tones.overall in MongoDB
}

// Add interface for timeline data item
interface TimelineDataItem {
  date: string;
  count: number;
  tone: number;
}

// Add interface for article data
interface ArticleData {
  title: string;
  url: string;
  date: string;
  source: string;
}

// Update CountryTimeStats interface
interface CountryTimeStats {
  articleCount: number;
  averageTone: number;
  timelineData: TimelineDataItem[];
  articles: ArticleData[];
}

// Add interface for export data
interface ExportData {
  [key: string]: string | number | Date;
}

const ARTICLES_PER_PAGE = 3;

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
  const [isSearching, setIsSearching] = useState(false);
  
  const chartRef = useRef<HTMLDivElement>(null);
  const articlesRef = useRef<HTMLDivElement>(null);

  // Store initial data state
  const [initialTimeStats, setInitialTimeStats] = useState<CountryTimeStats | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [showAllArticles, setShowAllArticles] = useState(false);

  // Format articles for export
  const getFormattedArticles = (articles: ArticleData[]): ExportData[] => {
    return articles.map(article => ({
      title: article.title,
      url: article.url,
      date: article.date,
      source: Array.isArray(article.source) ? article.source.join(", ") : article.source
    }));
  };

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

  // Format dates for API call
  const formatDateForAPI = (date: Date | undefined, isEndDate: boolean = false): Date | undefined => {
    if (!date) return undefined;
    
    const formattedDate = new Date(date);
    if (isEndDate) {
      formattedDate.setHours(23, 59, 59, 999);
    } else {
      formattedDate.setHours(0, 0, 0, 0);
    }
    return formattedDate;
  };

  // Handle search button click
  const handleSearch = () => {
    if (!dateError && validateDates(startDate, endDate)) {
      setIsSearching(true);
      fetchData(false);
    }
  };

  // Reset filters
  const handleReset = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    setDateError(null);
    // Restore the initial data instead of fetching new data
    if (initialTimeStats) {
      setTimeStats(initialTimeStats);
    }
  };

  // Fetch data function
  const fetchData = async (isInitialFetch: boolean = false) => {
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

      try {
        // Format dates for API call
        const apiStartDate = formatDateForAPI(startDate);
        const apiEndDate = formatDateForAPI(endDate, true);
        
        const timeStatsData = await getCountryTimeStats(iso2, apiStartDate, apiEndDate);
        console.log('Raw timeStats data:', timeStatsData);
        
        // Process the timeline data to ensure dates are properly formatted
        if (timeStatsData.timelineData && timeStatsData.timelineData.length > 0) {
          console.log('Processing timeline data:', timeStatsData.timelineData);
          timeStatsData.timelineData = timeStatsData.timelineData
            .map((item: RawTimelineItem) => {
              // Ensure we have valid data
              if (!item.date || typeof item.count !== 'number') {
                console.warn('Invalid timeline item:', item);
                return null;
              }
              const timelineItem: TimelineDataItem = {
                date: item.date,
                count: Number(item.count),
                tone: Number(item.tone || 0)
              };
              return timelineItem;
            })
            .filter((item): item is TimelineDataItem => item !== null);
          console.log('Processed timeline data:', timeStatsData.timelineData);
        }

        // Ensure unique articles by title
        if (timeStatsData.articles) {
          const uniqueArticles = new Map();
          timeStatsData.articles = timeStatsData.articles.filter(article => {
            if (uniqueArticles.has(article.title)) {
              return false;
            }
            uniqueArticles.set(article.title, true);
            return true;
          });
        }
        
        // Store initial data if this is the initial fetch
        if (isInitialFetch) {
          setInitialTimeStats(timeStatsData);
        }
        
        setTimeStats(timeStatsData);
      } catch (timeStatsError) {
        // If we fail to get time stats, just set empty stats
        const emptyStats = {
          articleCount: 0,
          averageTone: 0,
          timelineData: [] as TimelineDataItem[],
          articles: [] as ArticleData[]
        };
        setTimeStats(emptyStats);
        if (isInitialFetch) {
          setInitialTimeStats(emptyStats);
        }
      }
    } catch (error) {
      if (error instanceof Error && error.message.includes('not found')) {
        setError('Country not found');
      } else {
        console.error("Error fetching data:", error);
        const emptyStats = {
          articleCount: 0,
          averageTone: 0,
          timelineData: [] as TimelineDataItem[],
          articles: [] as ArticleData[]
        };
        setTimeStats(emptyStats);
        if (isInitialFetch) {
          setInitialTimeStats(emptyStats);
        }
      }
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    if (iso2) {
      fetchData(true); // Pass true to indicate this is the initial fetch
    }
  }, [iso2]);

  // Calculate total pages
  const getTotalPages = (articles: ArticleData[]) => {
    return Math.ceil(articles.length / ARTICLES_PER_PAGE);
  };

  // Get current articles to display
  const getCurrentArticles = (articles: ArticleData[]) => {
    const startIndex = (currentPage - 1) * ARTICLES_PER_PAGE;
    return articles.slice(startIndex, startIndex + ARTICLES_PER_PAGE);
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  // Toggle show all articles
  const toggleShowAll = () => {
    setShowAllArticles(!showAllArticles);
    setCurrentPage(1);
  };

  // Reset pagination when timeStats changes
  useEffect(() => {
    setCurrentPage(1);
  }, [timeStats]);

  if (loading && !isSearching) {
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
      if (value < 300) return "Medium";
      if (value < 500) return "High";
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
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <CardTitle className="text-2xl md:text-3xl flex items-center">
                  <Globe className="mr-3 h-6 w-6" />
                  {country.name}
                </CardTitle>
                <div className="flex flex-col md:flex-row items-start md:items-end gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Start Date</label>
                    <DatePicker date={startDate} setDate={handleStartDateChange} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Date</label>
                    <DatePicker date={endDate} setDate={handleEndDateChange} />
                  </div>
                  <div className="flex gap-2 self-end">
                    <Button 
                      onClick={handleSearch}
                      disabled={!!dateError || loading}
                      className="whitespace-nowrap"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-current mr-2"></div>
                          Searching...
                        </>
                      ) : (
                        'Search'
                      )}
                    </Button>
                    {(startDate || endDate) && (
                      <Button 
                        variant="outline" 
                        onClick={handleReset}
                        disabled={loading}
                      >
                        Reset
                      </Button>
                    )}
                  </div>
                </div>
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
          
          {loading ? (
            <Card className="lg:col-span-3 shadow-md">
              <CardContent>
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-lg">Loading data...</p>
                </div>
              </CardContent>
            </Card>
          ) : (!timeStats || timeStats.articleCount === 0) ? (
            <Card className="lg:col-span-3 shadow-md">
              <CardContent>
                <div className="text-center py-12">
                  <FileX className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Articles Found</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    {startDate || endDate ? 
                      `No articles found for ${country.name} in the selected date range.` :
                      `No antisemitic articles have been detected for ${country.name}.`
                    }
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
                      <LineChart
                        data={timeStats.timelineData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fill: '#6B7280' }}
                          tickFormatter={(value) => new Date(value).toLocaleDateString()}
                        />
                        <YAxis 
                          yAxisId="left" 
                          tick={{ fill: '#6B7280' }}
                          label={{ 
                            value: 'Number of Articles', 
                            angle: -90, 
                            position: 'insideLeft',
                            style: { fill: '#6B7280' }
                          }} 
                        />
                        <YAxis 
                          yAxisId="right" 
                          orientation="right"
                          tick={{ fill: '#6B7280' }}
                          label={{ 
                            value: 'Average Tone', 
                            angle: 90, 
                            position: 'insideRight',
                            style: { fill: '#6B7280' }
                          }} 
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'rgba(17, 24, 39, 0.8)',
                            border: '1px solid #374151',
                            borderRadius: '6px',
                            color: '#F3F4F6'
                          }}
                          formatter={(value: number, name: string) => {
                            if (name === 'Articles') return [`${value} articles`, name];
                            if (name === 'Tone') {
                              const color = value >= 0 ? '#10B981' : '#EF4444';
                              return [
                                <span style={{ color }}>
                                  {value.toFixed(2)}
                                </span>,
                                'Tone'
                              ];
                            }
                            return [value, name];
                          }}
                          labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        />
                        <Legend 
                          verticalAlign="top" 
                          height={36}
                          wrapperStyle={{
                            paddingBottom: '20px'
                          }}
                        />
                        <ReferenceLine 
                          y={0} 
                          yAxisId="right"
                          stroke="#374151" 
                          strokeDasharray="3 3"
                        />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="count"
                          name="Articles"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 6 }}
                        />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="tone"
                          name="Tone"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 6 }}
                        />
                        <Brush 
                          dataKey="date"
                          height={30}
                          stroke="#374151"
                          tickFormatter={(value) => new Date(value).toLocaleDateString()}
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
                  <div className="flex items-center gap-2">
                    <ExportButton
                      targetRef={articlesRef}
                      type="table"
                      data={getFormattedArticles(timeStats.articles)}
                      filename={`${country.name}-articles`}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4" ref={articlesRef}>
                    {getCurrentArticles(timeStats.articles).map((article, index) => (
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
                  
                  {timeStats.articles.length > ARTICLES_PER_PAGE && (
                    <div className="mt-4 flex justify-center items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm">
                        Page {currentPage} of {getTotalPages(timeStats.articles)}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === getTotalPages(timeStats.articles)}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
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

