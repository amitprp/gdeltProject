
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlobalStats as GlobalStatsType } from '@/services/dataService';
import { AlertTriangle, BarChart3, Globe, TrendingUp } from 'lucide-react';

interface GlobalStatsCardProps {
  data: GlobalStatsType;
}

const GlobalStatsCard: React.FC<GlobalStatsCardProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Total Antisemitic Articles</CardTitle>
          <Globe className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.totalArticles.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            Tracked across {data.continents.length} continents
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Average Per Country</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{Math.round(data.averagePerCountry).toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            From {data.topCountries.length} monitored countries
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Highest Concentration</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.topCountries[0]?.name || "N/A"}</div>
          <p className="text-xs text-muted-foreground">
            {data.topCountries[0]?.value.toLocaleString() || 0} articles detected
          </p>
        </CardContent>
      </Card>
      
      <Card className="shadow-md">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Most Affected Continent</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          {data.continents.length > 0 ? (
            <>
              <div className="text-2xl font-bold">
                {[...data.continents].sort((a, b) => b.totalArticles - a.totalArticles)[0]?.name}
              </div>
              <p className="text-xs text-muted-foreground">
                {[...data.continents].sort((a, b) => b.totalArticles - a.totalArticles)[0]?.totalArticles.toLocaleString()} articles
              </p>
            </>
          ) : (
            <div className="text-2xl font-bold">N/A</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default GlobalStatsCard;
