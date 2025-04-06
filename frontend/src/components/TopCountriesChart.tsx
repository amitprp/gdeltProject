
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CountryData } from '@/services/dataService';
import { useNavigate } from 'react-router-dom';

interface TopCountriesChartProps {
  data: CountryData[];
}

const TopCountriesChart: React.FC<TopCountriesChartProps> = ({ data }) => {
  const navigate = useNavigate();

  const handleBarClick = (data: any) => {
    if (data && data.iso2) {
      navigate(`/country/${data.iso2}`);
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const country = data.find(c => c.name === label);
      
      return (
        <div className="bg-white p-3 shadow-md rounded-md border">
          <p className="font-medium">{label}</p>
          <p className="text-sm">{`Articles: ${payload[0].value}`}</p>
          <p className="text-xs text-muted-foreground mt-1">Click to view details</p>
        </div>
      );
    }
    return null;
  };

  const chartData = data.map(country => ({
    name: country.name,
    articles: country.value,
    iso2: country.iso2
  }));

  return (
    <Card className="shadow-md">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Top Countries by Antisemitic Articles</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
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
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis 
                dataKey="name"
                tick={{ fontSize: 12 }}
                axisLine={false}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="articles" 
                fill="#3b82f6" 
                radius={[4, 4, 0, 0]}
                onClick={handleBarClick}
                cursor="pointer" 
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default TopCountriesChart;
