import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getGlobalStats, getColorByValue, CountryData } from '@/services/dataService';
import { Loader2, Globe } from 'lucide-react';

// Your Mapbox public token
const MAPBOX_TOKEN = 'pk.eyJ1Ijoia29iaXphIiwiYSI6ImNtOHZocDR6YTA1eGgybnNmdmRleG42bWYifQ.zEKcf1l2K12RHq3ZnrxXOA';

const WorldMap: React.FC = () => {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLoadButton, setShowLoadButton] = useState(true);
  const [countryData, setCountryData] = useState<CountryData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const stats = await getGlobalStats();
        console.log('Fetched country data:', stats.topCountries.map(country => ({
          name: country.name,
          code: country.code,
          value: country.value
        })));
        setCountryData(stats.topCountries);
      } catch (error) {
        console.error('Error fetching country data:', error);
      }
    };
    fetchData();
  }, []);

  const initializeMap = useCallback(() => {
    if (!mapContainer.current) return;

    try {
      if (map.current) {
        map.current.remove();
      }

      mapboxgl.accessToken = MAPBOX_TOKEN;

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

        // Only add the data-driven layer if we have country data
        if (countryData.length > 0) {
          console.log('Applying colors to countries with data:', countryData.map(country => ({
            name: country.name,
            code: country.code,
            value: country.value,
            color: country.value <= 100 ? '#e0f2fe' :   // Low (0-100)
                   country.value <= 300 ? '#38bdf8' :   // Medium (101-300)
                   country.value <= 500 ? '#0369a1' :   // High (301-500)
                   '#831843'                            // Severe (501+)
          })));

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
                  country.value <= 100 ? '#e0f2fe' :   // Low (0-100)
                  country.value <= 300 ? '#38bdf8' :   // Medium (101-300)
                  country.value <= 500 ? '#0369a1' :   // High (301-500)
                  '#831843'                            // Severe (501+)
                ]).flat(),
                'transparent'  // default color for countries not in our dataset
              ],
              'fill-opacity': 0.7
            }
          });

          // Add interactivity
          map.current.on('mousemove', 'country-fills-data', (e) => {
            if (!e.features || e.features.length === 0) return;
            
            map.current!.getCanvas().style.cursor = 'pointer';
            
            const feature = e.features[0];
            const countryCode = feature.properties?.iso_3166_1_alpha_2;
            const countryInfo = countryData.find(c => c.code === countryCode);
            
            if (countryInfo) {
              const popup = new mapboxgl.Popup({
                closeButton: false,
                closeOnClick: false
              });
              
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
            const popups = document.getElementsByClassName('mapboxgl-popup');
            while (popups[0]) {
              popups[0].remove();
            }
          });
          
          map.current.on('click', 'country-fills-data', (e) => {
            if (!e.features || e.features.length === 0) return;
            
            const feature = e.features[0];
            console.log('Feature properties:', feature.properties); // Debug log to see all properties
            
            // Try different ways to access the country code
            const countryCode = feature.properties?.['iso_3166_1_alpha_2'] || 
                              feature.properties?.['ISO_3166_1_ALPHA_2'] ||
                              feature.properties?.['iso_3166_1'];
                              
            console.log('Clicked country code:', countryCode); // Debug log
            
            if (countryCode) {
              const countryInfo = countryData.find(c => c.code === countryCode);
              if (countryInfo) {
                console.log('Found country info:', countryInfo); // Debug log
                navigate(`/country/${countryCode}`);
              } else {
                console.log('No data found for country:', countryCode); // Debug log
              }
            }
          });
        }

        setLoading(false);
      });
    } catch (error) {
      console.error('Error initializing map:', error);
      setLoading(false);
    }
  }, [countryData, navigate]);

  const handleLoadMap = () => {
    setShowLoadButton(false);
    initializeMap();
  };

  useEffect(() => {
    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  return (
    <Card className="w-full h-[600px] shadow-md">
      <CardContent className="p-0 relative overflow-hidden rounded-lg">
        {showLoadButton ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/90 p-6">
            <div className="text-center space-y-4">
              <Globe className="h-12 w-12 text-primary mx-auto" />
              <h3 className="text-xl font-semibold">Interactive World Map</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Click the button below to load the interactive map and explore antisemitism data by country.
              </p>
              <Button onClick={handleLoadMap} className="mt-4">
                Load Map
              </Button>
            </div>
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
              <span className="text-xs">Low (0-100)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-medium mr-2 rounded-sm"></div>
              <span className="text-xs">Medium (101-300)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-high mr-2 rounded-sm"></div>
              <span className="text-xs">High (301-500)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-severe mr-2 rounded-sm"></div>
              <span className="text-xs">Severe (501+)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WorldMap;
