import React, { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, TooltipProps } from 'recharts';
import { ContinentData } from '@/services/dataService';
import { ExportButton } from "@/components/ExportButton";

interface ContinentChartProps {
  data: ContinentData[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: {
      name: string;
      value: number;
    };
  }>;
}

// Cache interface
interface CachedContinentData {
  name: string;
  articles: number;
}

interface CacheData {
  continents: CachedContinentData[];
  timestamp: number;
}

const CACHE_KEY = 'continentDataCache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

// Updated modern color palette
const COLORS = [
  '#0ea5e9', // Vivid sky blue
  '#6366f1', // Indigo
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#f43f5e', // Rose
  '#14b8a6', // Teal
];

const RADIAN = Math.PI / 180;

const ContinentChart: React.FC<ContinentChartProps> = ({ data }) => {
  const [chartData, setChartData] = useState<{ name: string; value: number }[]>([]);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadData = () => {
      // Try to get cached data
      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const { continents, timestamp }: CacheData = JSON.parse(cachedData);
        const now = Date.now();
        
        // Check if cache is still valid (within 5 minutes)
        if (now - timestamp < CACHE_DURATION) {
          console.log('Using cached continent data');
          // Transform cached data to chart format
          setChartData(continents.map(continent => ({
            name: continent.name,
            value: continent.articles
          })));
          return;
        }
      }

      // If no cache or cache expired, process new data
      if (data && data.length > 0) {
        // Prepare data for cache (only essential info)
        const continentsToCache: CachedContinentData[] = data.map(continent => ({
          name: continent.name,
          articles: continent.totalArticles
        }));

        // Save to cache
        const cacheData: CacheData = {
          continents: continentsToCache,
          timestamp: Date.now()
        };
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));

        // Set chart data
        setChartData(continentsToCache.map(continent => ({
          name: continent.name,
          value: continent.articles
        })));
      }
    };

    loadData();
  }, [data]);

  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      // Calculate percentage dynamically
      const total = chartData.reduce((sum, item) => sum + item.value, 0);
      const percentage = ((payload[0].value / total) * 100).toFixed(1);
      
      return (
        <div className="bg-white p-3 shadow-lg rounded-lg border">
          <p className="font-semibold text-gray-800">{`${payload[0].name}`}</p>
          <p className="text-sm text-gray-600">{`Articles: ${payload[0].value.toLocaleString()}`}</p>
          <p className="text-sm text-gray-600">{`Percentage: ${percentage}%`}</p>
        </div>
      );
    }
    return null;
  };

  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    index,
    name,
  }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    const percentage = (percent * 100).toFixed(0);
    
    // Only show label if percentage is greater than 5%
    if (percent < 0.05) return null;

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${percentage}%`}
      </text>
    );
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Anti-Israeli Articles by Continent</CardTitle>
        <ExportButton
          targetRef={chartRef}
          type="chart"
          filename="continent-distribution"
        />
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full" ref={chartRef}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={115}
                innerRadius={60}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                label={renderCustomizedLabel}
                strokeWidth={2}
                stroke="white"
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]}
                    className="hover:opacity-80 transition-opacity duration-300"
                  />
                ))}
              </Pie>
              <Tooltip 
                content={<CustomTooltip />}
                cursor={{ fill: 'var(--background)' }}
              />
              <Legend 
                layout="horizontal" 
                verticalAlign="bottom" 
                align="center"
                formatter={(value) => (
                  <span className="text-sm font-medium text-gray-700">{value}</span>
                )}
                wrapperStyle={{
                  paddingTop: '20px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default ContinentChart;
