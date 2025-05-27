import React, { useRef, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CountryData } from '@/services/dataService';
import { useNavigate } from 'react-router-dom';
import { ExportButton } from "@/components/ExportButton";

interface TopCountriesChartProps {
  data: CountryData[];
}

interface ChartDataPoint {
  name: string;
  articles: number;
  code: string;
  averageTone: number;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}

interface CachedData {
  data: ChartDataPoint[];
  timestamp: number;
}

const CACHE_KEY = 'topCountriesCache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

const TopCountriesChart: React.FC<TopCountriesChartProps> = ({ data }) => {
  const navigate = useNavigate();
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    const loadData = () => {
      // Try to get cached data
      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const { data: cachedChartData, timestamp }: CachedData = JSON.parse(cachedData);
        const now = Date.now();
        
        // Check if cache is still valid (within 5 minutes)
        if (now - timestamp < CACHE_DURATION) {
          console.log('Using cached top countries data');
          setChartData(cachedChartData);
          return;
        }
      }

      // If no cache or cache expired, process new data
      const newChartData = data
        .slice(0, 7)
        .map(country => ({
          name: country.name,
          articles: country.value,
          code: country.code,
          averageTone: country.averageTone
        }));

      // Save to cache
      const cacheData: CachedData = {
        data: newChartData,
        timestamp: Date.now()
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
      
      setChartData(newChartData);
    };

    loadData();
  }, [data]);

  const handleBarClick = (data: ChartDataPoint) => {
    if (data && data.code) {
      navigate(`/country/${data.code}`);
    }
  };

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      const country = chartData.find(c => c.name === label);
      
      return (
        <div className="bg-white p-3 shadow-md rounded-md border">
          <p className="font-medium">{label}</p>
          <p className="text-sm">{`Articles: ${payload[0].value}`}</p>
          <p className="text-sm">{`Average Tone: ${country?.averageTone.toFixed(2)}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Top 7 Countries by Antisemitic Articles</CardTitle>
        <ExportButton
          targetRef={chartRef}
          type="chart"
          filename="top-countries-chart"
        />
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full" ref={chartRef}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
              barSize={50}
            >
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1e40af" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis 
                dataKey="name"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                content={<CustomTooltip />}
                cursor={{ fill: 'var(--background)', opacity: 0.2 }}
              />
              <Bar 
                dataKey="articles" 
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
                onClick={handleBarClick}
                cursor="pointer"
                className="hover:opacity-90 transition-opacity duration-200"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default TopCountriesChart;
