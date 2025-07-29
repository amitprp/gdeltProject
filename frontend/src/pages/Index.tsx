import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WorldMap from '@/components/WorldMap';
import ContinentChart from '@/components/ContinentChart';
import TopCountriesChart from '@/components/TopCountriesChart';
import DailyAveragesChart from '@/components/DailyAveragesChart';
import GlobalStatsCard from '@/components/GlobalStats';
import { getGlobalStats, getDailyAverages, GlobalStats, DailyAverageResponse } from '@/services/dataService';
import { Loader2, ChartBarIcon, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

const Index = () => {
  const navigate = useNavigate();
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [dailyAverages, setDailyAverages] = useState<DailyAverageResponse>({ highest: [], lowest: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching data...');
        const [statsData, averagesData] = await Promise.all([
          getGlobalStats(),
          getDailyAverages()
        ]);
        console.log('Received global stats:', statsData);
        console.log('Received daily averages:', averagesData);
        setGlobalStats(statsData);
        setDailyAverages(averagesData);
        setError(null);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="mt-4 text-lg">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (error || !globalStats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
          <p className="mt-4 text-lg text-destructive">{error || "Failed to load data"}</p>
          <Button 
            className="mt-4" 
            onClick={() => window.location.reload()}
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
        <h1 className="text-3xl font-bold mb-2">Global Anti-Israeli Insights</h1>
        <p className="text-muted-foreground">
          Interactive dashboard showcasing anti-israeli article prevalence across the world
        </p>
        </div>
        <div className="flex gap-4">
          <Button
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2 px-6"
            onClick={() => navigate('/source-analysis')}
          >
            <ChartBarIcon className="w-5 h-5" />
            Source Analysis
          </Button>
          <Button
            size="lg"
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2 px-6"
            onClick={() => navigate('/trend-comparison')}
          >
            <Clock className="w-5 h-5" />
            Compare Time Periods
          </Button>
        </div>
      </div>

      <div className="mb-8">
        <GlobalStatsCard data={globalStats} />
      </div>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Interactive World Map</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Explore Anti-Israeli data by country. Click on any country to see detailed information.
        </p>
        <WorldMap />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Anti-Israeli by Continent</h2>
          <ContinentChart data={globalStats.continents} />
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Top Countries</h2>
          <TopCountriesChart data={globalStats.topCountries} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Daily Average by Country</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Average number of anti-israeli articles published daily. Toggle between highest and lowest averages.
          </p>
          <DailyAveragesChart data={dailyAverages} />
        </div>
      </div>
    </div>
  );
};

export default Index;
