
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getCountryData, getColorByValue, CountryData } from '@/services/dataService';
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, AlertTriangle, Globe, Newspaper } from 'lucide-react';
import { Progress } from "@/components/ui/progress";

const CountryDetail: React.FC = () => {
  const { iso2 = '' } = useParams<{ iso2: string }>();
  const navigate = useNavigate();
  const [country, setCountry] = useState<CountryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getCountryData(iso2);
        if (data) {
          setCountry(data);
        }
        setLoading(false);
      } catch (error) {
        console.error("Error fetching country data:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, [iso2]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-lg">Loading country data...</p>
        </div>
      </div>
    );
  }

  if (!country) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Button variant="outline" onClick={() => navigate('/')} className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
        </Button>
        
        <div className="text-center py-16">
          <AlertTriangle className="h-16 w-16 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Country Not Found</h2>
          <p className="text-muted-foreground mb-6">We couldn't find data for the requested country.</p>
          <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
        </div>
      </div>
    );
  }

  const getSeverityLabel = (value: number) => {
    if (value < 100) return "Low";
    if (value < 200) return "Medium";
    if (value < 300) return "High";
    return "Severe";
  };

  const getSeverityColor = (value: number) => {
    const colorClass = getColorByValue(value);
    return `bg-${colorClass}`;
  };

  const getProgressValue = (value: number) => {
    // Map the value to a percentage (assuming max is around 500)
    return Math.min(100, (value / 5));
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Button variant="outline" onClick={() => navigate('/')} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
      </Button>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-3 shadow-md">
          <CardHeader>
            <CardTitle className="text-2xl md:text-3xl flex items-center">
              <Globe className="mr-3 h-6 w-6" />
              {country.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row items-center justify-between">
              <div className="mb-4 md:mb-0">
                <div className="text-sm text-muted-foreground mb-1">Antisemitism Level</div>
                <div className="text-3xl font-bold flex items-center">
                  {getSeverityLabel(country.value)}
                  <span className={`ml-2 inline-block w-3 h-3 rounded-full ${getSeverityColor(country.value)}`}></span>
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-sm text-muted-foreground mb-1">Antisemitic Articles</div>
                <div className="text-3xl font-bold">{country.value.toLocaleString()}</div>
              </div>
              
              <div className="text-right">
                <div className="text-sm text-muted-foreground mb-1">ISO Code</div>
                <div className="text-xl font-mono">{country.iso2} / {country.id}</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="lg:col-span-2 shadow-md">
          <CardHeader>
            <CardTitle className="text-xl">Antisemitism Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Antisemitic Articles</span>
                  <span className="text-sm font-medium">{country.value}</span>
                </div>
                <Progress value={getProgressValue(country.value)} className="h-2" />
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 rounded-lg p-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Severity Rating</span>
                    <span className={`text-sm font-medium ${getSeverityColor(country.value)} text-white px-2 rounded`}>
                      {getSeverityLabel(country.value)}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Based on total article count relative to global average
                  </div>
                </div>
                
                <div className="bg-secondary/50 rounded-lg p-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Global Ranking</span>
                    <span className="text-sm font-medium">
                      {/* This would be dynamic in a real implementation */}
                      Top 20%
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Relative position among all monitored countries
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle className="text-xl flex items-center">
              <Newspaper className="mr-2 h-5 w-5" />
              Sample Articles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-muted-foreground text-sm">
                This section would display examples of antisemitic articles detected in {country.name}.
              </p>
              
              <div className="rounded-md border p-3">
                <h4 className="font-medium text-sm">Example Article #1</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Sample headline would appear here with publication date and source
                </p>
              </div>
              
              <div className="rounded-md border p-3">
                <h4 className="font-medium text-sm">Example Article #2</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Sample headline would appear here with publication date and source
                </p>
              </div>
              
              <div className="rounded-md border p-3">
                <h4 className="font-medium text-sm">Example Article #3</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Sample headline would appear here with publication date and source
                </p>
              </div>
              
              <Button variant="outline" className="w-full mt-2" disabled>
                View All Articles
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CountryDetail;
