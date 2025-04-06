
import React, { useEffect, useState } from 'react';
import WorldMap from '@/components/WorldMap';
import ContinentChart from '@/components/ContinentChart';
import TopCountriesChart from '@/components/TopCountriesChart';
import GlobalStatsCard from '@/components/GlobalStats';
import { getGlobalStats, GlobalStats } from '@/services/dataService';
import { Loader2 } from 'lucide-react';

const Index = () => {
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getGlobalStats();
        setGlobalStats(data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching global stats:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading || !globalStats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="mt-4 text-lg">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Global Antisemitism Insights</h1>
        <p className="text-muted-foreground">
          Interactive dashboard showcasing antisemitic article prevalence across the world
        </p>
      </div>

      <div className="mb-8">
        <GlobalStatsCard data={globalStats} />
      </div>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Interactive World Map</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Explore antisemitism data by country. Click on any country to see detailed information.
        </p>
        <WorldMap />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">Antisemitism by Continent</h2>
          <ContinentChart data={globalStats.continents} />
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Top Countries</h2>
          <TopCountriesChart data={globalStats.topCountries} />
        </div>
      </div>
    </div>
  );
};

export default Index;
