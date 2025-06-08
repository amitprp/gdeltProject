import React, { useRef, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DailyAverageData } from '@/services/dataService';
import { ExportButton } from "@/components/ExportButton";
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from 'lucide-react';

interface DailyAveragesChartProps {
  data: {
    highest: DailyAverageData[];
    lowest: DailyAverageData[];
  };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}

const DailyAveragesChart: React.FC<DailyAveragesChartProps> = ({ data }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [showHighest, setShowHighest] = useState(true);
  
  const chartData = (showHighest ? data.highest : data.lowest).map(item => ({
    name: item.name,
    average: item.averageArticles
  }));

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 shadow-md rounded-md border">
          <p className="font-medium">{label}</p>
          <p className="text-sm">{`Daily Average: ${payload[0].value.toFixed(2)} articles`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Daily Average by Country</CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHighest(!showHighest)}
            className="flex items-center gap-1"
          >
            <ArrowUpDown className="h-4 w-4" />
            {showHighest ? 'Show Lowest' : 'Show Highest'}
          </Button>
          <ExportButton
            targetRef={chartRef}
            type="chart"
            filename="daily-averages-chart"
          />
        </div>
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
                  <stop offset="0%" stopColor={showHighest ? "#1e40af" : "#9333ea"} />
                  <stop offset="100%" stopColor={showHighest ? "#3b82f6" : "#a855f7"} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis 
                dataKey="name"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                angle={-45}
                textAnchor="end"
                height={60}
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
                dataKey="average" 
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
                className="hover:opacity-90 transition-opacity duration-200"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default DailyAveragesChart; 