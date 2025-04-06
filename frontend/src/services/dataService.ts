
import convert from 'country-iso-2-to-3';

// Define types for our data
export interface CountryData {
  id: string;  // ISO3 code
  name: string;
  value: number;
  iso2: string;
}

export interface ContinentData {
  name: string;
  totalArticles: number;
  countries: CountryData[];
}

export interface GlobalStats {
  totalArticles: number;
  topCountries: CountryData[];
  continents: ContinentData[];
  averagePerCountry: number;
}

// This function would be replaced with your actual API call to the Python server
export const getAllRes = async (): Promise<Record<string, number>> => {
  // Simulating API response with sample data
  return {
    "US": 450,
    "GB": 320,
    "FR": 280,
    "DE": 310,
    "RU": 390,
    "IL": 420,
    "SA": 85,
    "EG": 110,
    "IR": 430,
    "CN": 150,
    "JP": 70,
    "AU": 130,
    "BR": 180,
    "CA": 220,
    "IN": 160,
    "ZA": 90,
    "SE": 75,
    "ES": 140,
    "IT": 160,
    "AR": 130,
    "MX": 100,
    "NO": 50,
    "FI": 40,
    "DK": 60,
    "NL": 95,
    "BE": 85,
    "PL": 120,
    "UA": 140,
    "TR": 190,
    "GR": 70,
  };
};

// Country name mapping
const countryNames: Record<string, string> = {
  "US": "United States",
  "GB": "United Kingdom",
  "FR": "France",
  "DE": "Germany",
  "RU": "Russia",
  "IL": "Israel",
  "SA": "Saudi Arabia",
  "EG": "Egypt",
  "IR": "Iran",
  "CN": "China",
  "JP": "Japan",
  "AU": "Australia",
  "BR": "Brazil",
  "CA": "Canada",
  "IN": "India",
  "ZA": "South Africa",
  "SE": "Sweden",
  "ES": "Spain",
  "IT": "Italy",
  "AR": "Argentina",
  "MX": "Mexico",
  "NO": "Norway",
  "FI": "Finland",
  "DK": "Denmark",
  "NL": "Netherlands",
  "BE": "Belgium",
  "PL": "Poland",
  "UA": "Ukraine",
  "TR": "Turkey",
  "GR": "Greece",
};

// Continent mapping
const countryContinents: Record<string, string> = {
  "US": "North America",
  "GB": "Europe",
  "FR": "Europe",
  "DE": "Europe",
  "RU": "Europe",
  "IL": "Asia",
  "SA": "Asia",
  "EG": "Africa",
  "IR": "Asia",
  "CN": "Asia",
  "JP": "Asia",
  "AU": "Oceania",
  "BR": "South America",
  "CA": "North America",
  "IN": "Asia",
  "ZA": "Africa",
  "SE": "Europe",
  "ES": "Europe",
  "IT": "Europe",
  "AR": "South America",
  "MX": "North America",
  "NO": "Europe",
  "FI": "Europe",
  "DK": "Europe",
  "NL": "Europe",
  "BE": "Europe",
  "PL": "Europe",
  "UA": "Europe",
  "TR": "Asia",
  "GR": "Europe",
};

// Function to process data into the format we need
export const processCountryData = async (): Promise<CountryData[]> => {
  const rawData = await getAllRes();
  
  return Object.entries(rawData).map(([iso2, value]) => {
    let iso3 = "";
    try {
      iso3 = convert(iso2);
    } catch (e) {
      console.warn(`Could not convert ${iso2} to ISO3`);
      iso3 = iso2;
    }
    
    return {
      id: iso3,
      name: countryNames[iso2] || iso2,
      value,
      iso2
    };
  });
};

// Group countries by continent
export const getDataByContinent = async (): Promise<ContinentData[]> => {
  const countries = await processCountryData();
  const continentMap = new Map<string, ContinentData>();
  
  countries.forEach(country => {
    const continent = countryContinents[country.iso2] || "Unknown";
    
    if (!continentMap.has(continent)) {
      continentMap.set(continent, {
        name: continent,
        totalArticles: 0,
        countries: []
      });
    }
    
    const continentData = continentMap.get(continent)!;
    continentData.countries.push(country);
    continentData.totalArticles += country.value;
  });
  
  return Array.from(continentMap.values());
};

// Get global statistics
export const getGlobalStats = async (): Promise<GlobalStats> => {
  const countries = await processCountryData();
  const continents = await getDataByContinent();
  
  const totalArticles = countries.reduce((sum, country) => sum + country.value, 0);
  const topCountries = [...countries].sort((a, b) => b.value - a.value).slice(0, 5);
  
  return {
    totalArticles,
    topCountries,
    continents,
    averagePerCountry: totalArticles / countries.length
  };
};

// Get data for a specific country
export const getCountryData = async (iso2: string): Promise<CountryData | undefined> => {
  const countries = await processCountryData();
  return countries.find(country => country.iso2 === iso2);
};

// Get color based on antisemitism level
export const getColorByValue = (value: number): string => {
  if (value < 100) return 'map-low';
  if (value < 200) return 'map-medium';
  if (value < 300) return 'map-high';
  return 'map-severe';
};
