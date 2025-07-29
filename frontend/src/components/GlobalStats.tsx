import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlobalStats as GlobalStatsType } from '@/services/dataService';
import { AlertTriangle, BarChart3, Globe, TrendingUp } from 'lucide-react';

interface GlobalStatsCardProps {
  data: GlobalStatsType;
}

interface CachedGlobalStats {
  totalArticles: number;
  averagePerCountry: number;
  highestConcentrationCountry: {
    name: string;
    value: number;
  };
  mostAffectedContinent: {
    name: string;
    totalArticles: number;
  };
  timestamp: number;
}

const CACHE_KEY = 'globalStatsCache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

const GlobalStatsCard: React.FC<GlobalStatsCardProps> = ({ data }) => {
  const [stats, setStats] = useState<CachedGlobalStats | null>(null);

  useEffect(() => {
    const loadData = () => {
      // Try to get cached data
      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const parsedCache: CachedGlobalStats = JSON.parse(cachedData);
        const now = Date.now();
        
        // Check if cache is still valid (within 5 minutes)
        if (now - parsedCache.timestamp < CACHE_DURATION) {
          console.log('Using cached global stats');
          setStats(parsedCache);
          return;
        }
      }

      // If no cache or cache expired, process new data
      const highestConcentrationCountry = data.topCountries[0] || { name: "N/A", value: 0 };
      const mostAffectedContinent = [...data.continents]
        .sort((a, b) => b.totalArticles - a.totalArticles)[0] || { name: "N/A", totalArticles: 0 };

      const newStats: CachedGlobalStats = {
        totalArticles: data.totalArticles,
        averagePerCountry: data.averagePerCountry,
        highestConcentrationCountry: {
          name: highestConcentrationCountry.name,
          value: highestConcentrationCountry.value
        },
        mostAffectedContinent: {
          name: mostAffectedContinent.name,
          totalArticles: mostAffectedContinent.totalArticles
        },
        timestamp: Date.now()
      };

      // Save to cache
      localStorage.setItem(CACHE_KEY, JSON.stringify(newStats));
      setStats(newStats);
    };

    loadData();
  }, [data]);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Total Anti-Israeli Articles</CardTitle>
          <Globe className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalArticles.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            Tracked across multiple continents
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Average Per Country</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{Math.round(stats.averagePerCountry).toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            From monitored countries
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Highest Concentration</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.highestConcentrationCountry.name}</div>
          <p className="text-xs text-muted-foreground">
            {stats.highestConcentrationCountry.value.toLocaleString()} articles detected
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Most Affected Continent</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.mostAffectedContinent.name}</div>
          <p className="text-xs text-muted-foreground">
            {stats.mostAffectedContinent.totalArticles.toLocaleString()} articles
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default GlobalStatsCard;
