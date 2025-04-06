
import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { processCountryData, getColorByValue } from '@/services/dataService';
import { Loader2, Globe } from 'lucide-react';

const WorldMap: React.FC = () => {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapboxToken, setMapboxToken] = useState<string>('');
  const [showTokenInput, setShowTokenInput] = useState(true);

  const initializeMap = async () => {
    if (!mapContainer.current || !mapboxToken) return;
    
    try {
      // Set mapbox token
      mapboxgl.accessToken = mapboxToken;
      
      // Initialize map with globe projection
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        zoom: 1.5,
        center: [0, 20],
        projection: 'globe',
        renderWorldCopies: false
      });

      // Add navigation controls
      map.current.addControl(
        new mapboxgl.NavigationControl(),
        'top-right'
      );

      // Add globe atmosphere if supported
      map.current.on('style.load', () => {
        // Add atmosphere and fog for globe effect
        if (map.current) {
          map.current.setFog({
            color: 'rgb(255, 255, 255)', // white
            'high-color': 'rgb(200, 200, 225)', // light blue
            'horizon-blend': 0.2,
            'space-color': 'rgb(25, 25, 40)', // dark blue
            'star-intensity': 0.6
          });
        }
      });

      // Load country data
      const countryData = await processCountryData();
      
      // Add country data to map on load
      map.current.on('load', () => {
        if (!map.current) return;
        
        // Add country fill layer if it doesn't exist
        if (!map.current.getSource('countries')) {
          map.current.addSource('countries', {
            type: 'vector',
            url: 'mapbox://mapbox.country-boundaries-v1',
          });
        
          // Add fill layer
          map.current.addLayer({
            id: 'country-fills',
            type: 'fill',
            source: 'countries',
            'source-layer': 'country_boundaries',
            paint: {
              'fill-color': 'rgba(200, 200, 200, 0.2)',
              'fill-outline-color': '#aaa',
            }
          });
          
          // Add highlighted fill layer for countries with data
          map.current.addLayer({
            id: 'country-fills-data',
            type: 'fill',
            source: 'countries',
            'source-layer': 'country_boundaries',
            paint: {
              'fill-color': [
                'case',
                ['boolean', ['feature-state', 'hasData'], false],
                ['string', ['feature-state', 'color'], 'rgba(200, 200, 200, 0.2)'],
                'rgba(200, 200, 200, 0.2)'
              ],
              'fill-opacity': 0.8,
              'fill-outline-color': '#aaa',
            }
          });
        }
        
        // Set feature states for countries with data
        countryData.forEach(country => {
          const color = getColorByValue(country.value);
          const colorValue = `rgb(var(--${color}))`;
          
          try {
            map.current?.setFeatureState(
              { source: 'countries', sourceLayer: 'country_boundaries', id: country.iso2 },
              { hasData: true, color: colorValue, value: country.value }
            );
          } catch (error) {
            console.warn(`Error setting feature state for ${country.name}:`, error);
          }
        });
        
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
          const countryInfo = countryData.find(c => c.iso2 === countryCode);
          
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
          const countryInfo = countryData.find(c => c.iso2 === countryCode);
          
          if (countryInfo) {
            navigate(`/country/${countryInfo.iso2}`);
          }
        });
        
        // Add a slow rotation animation for the globe
        const secondsPerRevolution = 180; // 3 minutes per rotation
        let userInteracting = false;
        
        function spinGlobe() {
          if (!map.current || userInteracting) return;
          
          const zoom = map.current.getZoom();
          if (zoom < 3) { // Only spin when zoomed out
            const center = map.current.getCenter();
            center.lng -= 0.2; // Slow rotation speed
            map.current.easeTo({ center, duration: 300, easing: (n) => n });
          }
        }

        // Start the animation
        const spinInterval = setInterval(spinGlobe, 300);
        
        // Stop spinning when user interacts
        map.current.on('mousedown', () => {
          userInteracting = true;
          clearInterval(spinInterval);
        });
        
        map.current.on('touchstart', () => {
          userInteracting = true;
          clearInterval(spinInterval);
        });
        
        // Resume spinning after a brief pause following interaction
        map.current.on('mouseup', () => {
          setTimeout(() => {
            userInteracting = false;
          }, 3000);
        });
        
        map.current.on('touchend', () => {
          setTimeout(() => {
            userInteracting = false;
          }, 3000);
        });
        
        setLoading(false);
      });
    } catch (error) {
      console.error("Error initializing map:", error);
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
              <span className="text-xs">Low (&lt;100)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-medium mr-2 rounded-sm"></div>
              <span className="text-xs">Medium (100-199)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-high mr-2 rounded-sm"></div>
              <span className="text-xs">High (200-299)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-map-severe mr-2 rounded-sm"></div>
              <span className="text-xs">Severe (300+)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WorldMap;
