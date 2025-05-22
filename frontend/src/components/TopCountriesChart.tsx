import React, { useRef } from 'react';
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

const TopCountriesChart: React.FC<TopCountriesChartProps> = ({ data }) => {
  const navigate = useNavigate();
  const chartRef = useRef<HTMLDivElement>(null);

  const handleBarClick = (data: ChartDataPoint) => {
    if (data && data.code) {
      navigate(`/country/${data.code}`);
    }
  };

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      const country = data.find(c => c.name === label);
      
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

  const chartData = data.map(country => ({
    name: country.name,
    articles: country.value,
    code: country.code,
    averageTone: country.averageTone
  }));

  // Add gradient definition
  const gradientOffset = () => {
    return 0.6;
  };

  return (
    <Card className="shadow-md">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Top Countries by Antisemitic Articles</CardTitle>
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
              barSize={40}
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
