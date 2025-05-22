import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { format } from "date-fns";
import { CalendarIcon, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { timeFrameComparison, TimeFrameData } from "@/services/trendComparison";
import BackToHome from "@/components/BackToHome";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import { ExportButton } from "@/components/ExportButton";

const TrendComparison = () => {
  const [timeFrame1Start, setTimeFrame1Start] = useState<Date>();
  const [timeFrame1End, setTimeFrame1End] = useState<Date>();
  const [timeFrame2Start, setTimeFrame2Start] = useState<Date>();
  const [timeFrame2End, setTimeFrame2End] = useState<Date>();
  const [comparisonData, setComparisonData] = useState<[TimeFrameData, TimeFrameData]>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const chartRef = useRef<HTMLDivElement>(null);

  const handleCompare = async () => {
    if (timeFrame1Start && timeFrame1End && timeFrame2Start && timeFrame2End) {
      setLoading(true);
      setError(undefined);

      // Client-side validation
      const now = new Date();
      if (timeFrame1Start > timeFrame1End || timeFrame2Start > timeFrame2End) {
        setError("Start date must be before end date");
        setLoading(false);
        return;
      }

      if (timeFrame1Start > now || timeFrame1End > now || 
          timeFrame2Start > now || timeFrame2End > now) {
        setError("Dates cannot be in the future");
        setLoading(false);
        return;
      }

      try {
        const data = await timeFrameComparison(
          timeFrame1Start,
          timeFrame1End,
          timeFrame2Start,
          timeFrame2End
        );
        setComparisonData(data);
      } catch (err) {
        let errorMessage = "Failed to fetch comparison data. Please try again.";
        if (err instanceof Error) {
          // Try to parse error message from API
          try {
            const apiError = JSON.parse(err.message);
            errorMessage = apiError.detail || err.message;
          } catch {
            errorMessage = err.message;
          }
        }
        setError(errorMessage);
        console.error("Error fetching comparison data:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="container mx-auto py-8">
      <BackToHome />
      <h1 className="text-3xl font-bold mb-8">Trend Comparison</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Time Frame 1 */}
        <Card>
          <CardHeader>
            <CardTitle>Time Frame 1</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col space-y-2">
              <span className="text-sm font-medium">Start Date</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !timeFrame1Start && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {timeFrame1Start ? format(timeFrame1Start, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={timeFrame1Start}
                    onSelect={setTimeFrame1Start}
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div className="flex flex-col space-y-2">
              <span className="text-sm font-medium">End Date</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !timeFrame1End && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {timeFrame1End ? format(timeFrame1End, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={timeFrame1End}
                    onSelect={setTimeFrame1End}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </CardContent>
        </Card>

        {/* Time Frame 2 */}
        <Card>
          <CardHeader>
            <CardTitle>Time Frame 2</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col space-y-2">
              <span className="text-sm font-medium">Start Date</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !timeFrame2Start && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {timeFrame2Start ? format(timeFrame2Start, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={timeFrame2Start}
                    onSelect={setTimeFrame2Start}
                  />
                </PopoverContent>
              </Popover>
            </div>
            <div className="flex flex-col space-y-2">
              <span className="text-sm font-medium">End Date</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !timeFrame2End && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {timeFrame2End ? format(timeFrame2End, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={timeFrame2End}
                    onSelect={setTimeFrame2End}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 flex justify-center">
        <Button
          size="lg"
          onClick={handleCompare}
          disabled={!timeFrame1Start || !timeFrame1End || !timeFrame2Start || !timeFrame2End || loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Comparing...
            </>
          ) : (
            "Compare Time Frames"
          )}
        </Button>
      </div>

      {error && (
        <div className="mt-8 p-4 bg-destructive/10 text-destructive rounded-md">
          {error}
        </div>
      )}

      {comparisonData && (
        <div className="mt-8 space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Comparison Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Time Frame 1</h3>
                  <p>
                    {format(comparisonData[0].startDate, "PPP")} -{" "}
                    {format(comparisonData[0].endDate, "PPP")}
                  </p>
                  <p className="text-2xl font-bold mt-2">
                    {comparisonData[0].articleCount} articles
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-2">Time Frame 2</h3>
                  <p>
                    {format(comparisonData[1].startDate, "PPP")} -{" "}
                    {format(comparisonData[1].endDate, "PPP")}
                  </p>
                  <p className="text-2xl font-bold mt-2">
                    {comparisonData[1].articleCount} articles
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Daily Article Frequency</CardTitle>
                <ExportButton
                  targetRef={chartRef}
                  type="chart"
                  filename="time-comparison"
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]" ref={chartRef}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(date) => format(new Date(date), "MMM d")}
                      allowDuplicatedCategory={false}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(date) => format(new Date(date), "PPP")}
                      formatter={(value) => [`${value} articles`]}
                    />
                    <Legend />
                    
                    {/* First Time Frame */}
                    <Line
                      name="Time Frame 1"
                      data={comparisonData[0].dailyData}
                      type="monotone"
                      dataKey="articleCount"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />

                    {/* Second Time Frame */}
                    <Line
                      name="Time Frame 2"
                      data={comparisonData[1].dailyData}
                      type="monotone"
                      dataKey="articleCount"
                      stroke="#16a34a"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TrendComparison; 