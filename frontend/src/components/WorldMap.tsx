import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getGlobalStats, getColorByValue, CountryData } from '@/services/dataService';
import { Loader2, Globe } from 'lucide-react';

const WorldMap: React.FC = () => {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapboxToken, setMapboxToken] = useState<string>('');
  const [showTokenInput, setShowTokenInput] = useState(true);
  const [countryData, setCountryData] = useState<CountryData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const stats = await getGlobalStats();
        setCountryData(stats.topCountries);
      } catch (error) {
        console.error('Error fetching country data:', error);
      }
    };
    fetchData();
  }, []);

  const initializeMap = async () => {
    if (!mapContainer.current || !mapboxToken) return;

    try {
      mapboxgl.accessToken = mapboxToken;

      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [0, 20],
        zoom: 1.5
      });

      map.current.on('load', () => {
        if (!map.current) return;

        // Add country fill layer
        map.current.addSource('country-boundaries', {
          type: 'vector',
          url: 'mapbox://mapbox.country-boundaries-v1'
        });

        map.current.addLayer({
          id: 'country-fills',
          type: 'fill',
          source: 'country-boundaries',
          'source-layer': 'country_boundaries',
          paint: {
            'fill-color': '#627BC1',
            'fill-opacity': 0.1
          }
        });

        // Add data-driven styling layer
        map.current.addLayer({
          id: 'country-fills-data',
          type: 'fill',
          source: 'country-boundaries',
          'source-layer': 'country_boundaries',
          paint: {
            'fill-color': [
              'match',
              ['get', 'iso_3166_1'],
              ...countryData.map(country => [
                country.code,
                country.value <= 10 ? '#e0f2fe' :  // map-low
                country.value <= 50 ? '#38bdf8' :  // map-medium
                country.value <= 100 ? '#0369a1' : // map-high
                '#831843'                          // map-severe
              ]).flat(),
              'transparent'  // default color for countries not in our dataset
            ],
            'fill-opacity': 0.7
          }
        });

        setLoading(false);
        
        // Show popup on hover
        const popup = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false
        });
        
        map.current.on('mousemove', 'country-fills-data', (e) => {
          if (!e.features || e.features.length === 0) return;
          
          map.current!.getCanvas().style.cursor = 'pointer';
          
          const feature = e.features[0];
          const countryCode = feature.properties?.iso_3166_1;
          const countryInfo = countryData.find(c => c.code === countryCode);
          
          if (countryInfo) {
            const value = countryInfo.value;
            popup.setLngLat(e.lngLat)
              .setHTML(`
                <div class="font-bold">${countryInfo.name}</div>
                <div>Antisemitic Articles: ${value}</div>
              `)
              .addTo(map.current!);
          }
        });
        
        map.current.on('mouseleave', 'country-fills-data', () => {
          map.current!.getCanvas().style.cursor = '';
          popup.remove();
        });
        
        // Navigate to country page on click
        map.current.on('click', 'country-fills-data', (e) => {
          if (!e.features || e.features.length === 0) return;
          
          const countryCode = e.features[0].properties?.iso_3166_1;
          console.log('Clicked country code:', countryCode); // Debug log
          
          if (countryCode) {
            console.log('Navigating to country:', countryCode); // Debug log
            navigate(`/country/${countryCode}`);
          }
        });
      });
    } catch (error) {
      console.error('Error initializing map:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mapboxToken) {
      setShowTokenInput(false);
      initializeMap();
    }
    
    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, [mapboxToken]);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const token = new FormData(form).get('token') as string;
    if (token) {
      setMapboxToken(token);
    }
  };

  return (
    <Card className="w-full h-[600px] shadow-md">
      <CardContent className="p-0 relative overflow-hidden rounded-lg">
        {showTokenInput ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/90 p-6">
            <form onSubmit={handleTokenSubmit} className="w-full max-w-md space-y-4">
              <div className="flex justify-center mb-4">
                <Globe className="h-12 w-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-center mb-4">Enter Mapbox Token</h3>
              <p className="text-sm text-muted-foreground text-center">
                Please enter your Mapbox public token to display the interactive globe.
                You can get one from <a href="https://mapbox.com/" target="_blank" rel="noreferrer" className="text-primary underline">mapbox.com</a>
              </p>
              <input
                type="text"
                name="token"
                className="w-full p-2 border rounded-md"
                placeholder="Enter your Mapbox public token"
                required
              />
              <Button type="submit" className="w-full">
                Load Globe
              </Button>
            </form>
          </div>
        ) : loading ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/50">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : null}
        <div ref={mapContainer} className="w-full h-[600px]" />
        <div className="absolute bottom-4 right-4 bg-white shadow-lg rounded-md p-3 z-10">
          <h4 className="font-medium text-sm mb-2">Antisemitism Level</h4>
          <div className="space-y-1">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-low mr-2 rounded-sm"></div>
              <span className="text-xs">Low (0-10)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-medium mr-2 rounded-sm"></div>
              <span className="text-xs">Medium (11-50)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-high mr-2 rounded-sm"></div>
              <span className="text-xs">High (51-100)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-severe mr-2 rounded-sm"></div>
              <span className="text-xs">Severe (100+)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WorldMap;
