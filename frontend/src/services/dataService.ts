import convert from 'country-iso-2-to-3';

// Cache variables for global stats
let cachedGlobalStats: GlobalStats | null = null;
let lastFetchTime: number | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

// Cache for country details
const countryCache: Record<string, CountryData> = {};
const countryTimeStatsCache: Record<string, { data: CountryTimeStats; timestamp: number }> = {};
const COUNTRY_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Define types for our data
export interface CountryData {
  id: string;  // ISO3 code
  name: string;
  value: number;
  iso2: string;
  code: string;
  averageTone: number;
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

export interface CountryTimeStats {
  articleCount: number;
  averageTone: number;
  timelineData: {
    date: string;
    count: number;
    tone: number;
  }[];
  articles: {
    title: string;
    date: string;
    source: string;
    url: string;
  }[];
}

export interface GroupedSourceData {
  name: string;
  source?: string;  // Optional source field for country grouping
  articleCount: number;
  averageTone: number;
  lastArticleDate: string;
  recentArticles: {
    title: string;
    url: string;
    date: string;
    tone: number;
  }[];
}

export interface GroupedSourceResponse {
  groups: GroupedSourceData[];
}

export interface SourceAnalysisFilters {
  startDate?: Date;
  endDate?: Date;
  country?: string;
  author?: string;
}

export interface SourceAnalysisData {
  source: string;
  pageAuthors?: string;  // Optional pageAuthors field
  country: string;
  articleCount: number;
  averageTone: number;
  lastArticleDate: string;
  recentArticles: {
    title: string;
    url: string;
    date: string;
    tone: number;
  }[];
}

export interface DailyAverageData {
  country: string;
  name: string;
  averageArticles: number;
  totalDays: number;
}

export interface DailyAverageResponse {
  highest: DailyAverageData[];
  lowest: DailyAverageData[];
}

// Country name mapping
const countryNames: Record<string, string> = {
  "US": "United States",
  "UK": "United Kingdom",
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
  // North America
  "US": "North America",
  "CA": "North America",
  "MX": "North America",
  "BM": "North America",
  "BS": "North America",
  "BB": "North America",
  "BZ": "North America",
  "CR": "North America",
  "CU": "North America",
  "DM": "North America",
  "DO": "North America",
  "SV": "North America",
  "GD": "North America",
  "GT": "North America",
  "HT": "North America",
  "HN": "North America",
  "JM": "North America",
  "NI": "North America",
  "PA": "North America",
  "KN": "North America",
  "LC": "North America",
  "VC": "North America",
  "TT": "North America",
  
  // South America
  "AR": "South America",
  "BR": "South America",
  "BO": "South America",
  "CL": "South America",
  "CO": "South America",
  "EC": "South America",
  "GY": "South America",
  "PY": "South America",
  "PE": "South America",
  "SR": "South America",
  "UY": "South America",
  "VE": "South America",

  // Europe
  "UK": "Europe",
  "FR": "Europe",
  "DE": "Europe",
  "RU": "Europe",
  "SE": "Europe",
  "ES": "Europe",
  "IT": "Europe",
  "NO": "Europe",
  "FI": "Europe",
  "DK": "Europe",
  "NL": "Europe",
  "BE": "Europe",
  "PL": "Europe",
  "UA": "Europe",
  "GR": "Europe",
  "AL": "Europe",
  "AD": "Europe",
  "AT": "Europe",
  "BY": "Europe",
  "BA": "Europe",
  "BG": "Europe",
  "HR": "Europe",
  "CY": "Europe",
  "CZ": "Europe",
  "EE": "Europe",
  "HU": "Europe",
  "IS": "Europe",
  "IE": "Europe",
  "LV": "Europe",
  "LI": "Europe",
  "LT": "Europe",
  "LU": "Europe",
  "MT": "Europe",
  "MD": "Europe",
  "MC": "Europe",
  "ME": "Europe",
  "MK": "Europe",
  "PT": "Europe",
  "RO": "Europe",
  "RS": "Europe",
  "SK": "Europe",
  "SI": "Europe",
  "CH": "Europe",
  "VA": "Europe",

  // Asia
  "IL": "Asia",
  "SA": "Asia",
  "IR": "Asia",
  "CN": "Asia",
  "JP": "Asia",
  "IN": "Asia",
  "TR": "Asia",
  "AF": "Asia",
  "AM": "Asia",
  "AZ": "Asia",
  "BH": "Asia",
  "BD": "Asia",
  "BN": "Asia",
  "KH": "Asia",
  "GE": "Asia",
  "ID": "Asia",
  "IQ": "Asia",
  "JO": "Asia",
  "KZ": "Asia",
  "KW": "Asia",
  "KG": "Asia",
  "LA": "Asia",
  "LB": "Asia",
  "MY": "Asia",
  "MV": "Asia",
  "MN": "Asia",
  "MM": "Asia",
  "NP": "Asia",
  "OM": "Asia",
  "PK": "Asia",
  "PH": "Asia",
  "QA": "Asia",
  "SG": "Asia",
  "KR": "Asia",
  "LK": "Asia",
  "SY": "Asia",
  "TW": "Asia",
  "TJ": "Asia",
  "TH": "Asia",
  "TM": "Asia",
  "AE": "Asia",
  "UZ": "Asia",
  "VN": "Asia",
  "YE": "Asia",

  // Africa
  "EG": "Africa",
  "ZA": "Africa",
  "DZ": "Africa",
  "AO": "Africa",
  "BJ": "Africa",
  "BW": "Africa",
  "BF": "Africa",
  "BI": "Africa",
  "CM": "Africa",
  "CV": "Africa",
  "CF": "Africa",
  "TD": "Africa",
  "KM": "Africa",
  "CG": "Africa",
  "CD": "Africa",
  "DJ": "Africa",
  "GQ": "Africa",
  "ER": "Africa",
  "ET": "Africa",
  "GA": "Africa",
  "GM": "Africa",
  "GH": "Africa",
  "GN": "Africa",
  "GW": "Africa",
  "KE": "Africa",
  "LS": "Africa",
  "LR": "Africa",
  "LY": "Africa",
  "MG": "Africa",
  "MW": "Africa",
  "ML": "Africa",
  "MR": "Africa",
  "MU": "Africa",
  "MA": "Africa",
  "MZ": "Africa",
  "NA": "Africa",
  "NE": "Africa",
  "NG": "Africa",
  "RW": "Africa",
  "ST": "Africa",
  "SN": "Africa",
  "SC": "Africa",
  "SL": "Africa",
  "SO": "Africa",
  "SS": "Africa",
  "SD": "Africa",
  "SZ": "Africa",
  "TZ": "Africa",
  "TG": "Africa",
  "TN": "Africa",
  "UG": "Africa",
  "EH": "Africa",
  "ZM": "Africa",
  "ZW": "Africa",

  // Oceania
  "AU": "Oceania",
  "FJ": "Oceania",
  "KI": "Oceania",
  "MH": "Oceania",
  "FM": "Oceania",
  "NR": "Oceania",
  "NZ": "Oceania",
  "PW": "Oceania",
  "PG": "Oceania",
  "WS": "Oceania",
  "SB": "Oceania",
  "TO": "Oceania",
  "TV": "Oceania",
  "VU": "Oceania"
};

// Reverse mapping from country name to code
const countryNameToCode: Record<string, string> = Object.entries(countryNames).reduce((acc, [code, name]) => {
  acc[name.toLowerCase()] = code;
  return acc;
}, {} as Record<string, string>);

// Get color based on number of antisemitic articles
export const getColorByValue = (value: number): string => {
  // Color ranges based on article count
  if (value <= 10) return 'map-low';        // 0-10 articles
  if (value <= 50) return 'map-medium';     // 11-50 articles
  if (value <= 100) return 'map-high';      // 51-100 articles
  return 'map-severe';                      // More than 100 articles
};

interface APICountryResponse {
  code: string;
  name: string;
  value: number;
  averageTone: number;
}

// Get global statistics
export const getGlobalStats = async (): Promise<GlobalStats> => {
  // Return cached data if available and not expired
  if (cachedGlobalStats && lastFetchTime && (Date.now() - lastFetchTime < CACHE_DURATION)) {
    return cachedGlobalStats;
  }

  try {
    const response = await fetch('/api/v1/articles/global-stats');
    if (!response.ok) {
      throw new Error('Failed to fetch global stats');
    }
    
    const data = await response.json();
    console.log('Received global stats:', data);
    
    // Transform the data into the expected format
    const globalStats: GlobalStats = {
      totalArticles: data.totalArticles,
      topCountries: data.countries.map((country: APICountryResponse) => ({
        ...country,
        id: country.code,
        iso2: country.code,
        value: country.value
      })),
      continents: [],
      averagePerCountry: data.averagePerCountry
    };

    // Group countries by continent
    const continentMap = new Map<string, ContinentData>();
    globalStats.topCountries.forEach(country => {
      const continent = countryContinents[country.code] || "Unknown";
      
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

    globalStats.continents = Array.from(continentMap.values());

    // Cache the results
    cachedGlobalStats = globalStats;
    lastFetchTime = Date.now();
    
    return globalStats;
  } catch (error) {
    console.error('Error fetching global stats:', error);
    return {
      totalArticles: 0,
      topCountries: [],
      continents: [],
      averagePerCountry: 0
    };
  }
};

// Get data for a specific country
export const getCountryData = async (iso2: string): Promise<CountryData | undefined> => {
  // Return cached data if available
  if (countryCache[iso2]) {
    return countryCache[iso2];
  }

  try {
    const response = await fetch(`/api/v1/articles/country/${iso2}`);
    if (!response.ok) {
      if (response.status === 404) {
        return undefined;
      }
      throw new Error('Failed to fetch country data');
    }
    
    const data = await response.json();
    countryCache[iso2] = data;
    return data;
  } catch (error) {
    console.error('Error fetching country data:', error);
    return undefined;
  }
};

export const getCountryTimeStats = async (
  iso2: string,
  startDate?: Date,
  endDate?: Date
): Promise<CountryTimeStats> => {
  const cacheKey = `${iso2}-${startDate?.toISOString() || ''}-${endDate?.toISOString() || ''}`;
  const cachedData = countryTimeStatsCache[cacheKey];
  
  // Return cached data if available and not expired
  if (cachedData && (Date.now() - cachedData.timestamp < COUNTRY_CACHE_DURATION)) {
    return cachedData.data;
  }

  try {
    const params = new URLSearchParams({
      ...(startDate && { start_date: startDate.toISOString() }),
      ...(endDate && { end_date: endDate.toISOString() })
    });

    const response = await fetch(`/api/v1/articles/country/${iso2}/time-stats?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch country time stats');
    }

    const data = await response.json();
    
    // Cache the results
    countryTimeStatsCache[cacheKey] = {
      data,
      timestamp: Date.now()
    };
    
    return data;
  } catch (error) {
    console.error('Error fetching country time stats:', error);
    return {
      articleCount: 0,
      averageTone: 0,
      timelineData: [],
      articles: []
    };
  }
};

export const getGroupedSources = async (
  groupBy: "author" | "country",
  startDate?: Date,
  endDate?: Date
): Promise<GroupedSourceData[]> => {
  try {
    const params = new URLSearchParams({
      group_by: groupBy,
      ...(startDate && { start_date: startDate.toISOString() }),
      ...(endDate && { end_date: endDate.toISOString() })
    });

    const response = await fetch(`/api/v1/sources/grouped?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch grouped sources');
    }

    const data: GroupedSourceResponse = await response.json();
    return data.groups;
  } catch (error) {
    console.error('Error fetching grouped sources:', error);
    return [];
  }
};

export const getSourceAnalysis = async (
  filters: SourceAnalysisFilters
): Promise<SourceAnalysisData[]> => {
  try {
    console.log('Sending source analysis request with filters:', filters);

    // Convert country name to ISO code if it exists
    let countryFilter = filters.country;
    if (filters.country) {
      const countryLower = filters.country.toLowerCase();
      if (countryNameToCode[countryLower]) {
        countryFilter = countryNameToCode[countryLower];
      }
    }

    const response = await fetch('/api/v1/sources/analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        startDate: filters.startDate?.toISOString(),
        endDate: filters.endDate?.toISOString(),
        country: countryFilter,
        author: filters.author,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch source analysis');
    }

    const data = await response.json();
    console.log('Received source analysis response:', data);
    return data.sources || [];
  } catch (error) {
    console.error('Error fetching source analysis:', error);
    return [];
  }
};

let cachedTopCountries: CountryData[] | null = null;

export const getTopCountries = async (): Promise<CountryData[]> => {
  // Return cached data if available
  if (cachedTopCountries) {
    return cachedTopCountries;
  }

  try {
    const response = await fetch('/api/countries/top');
    if (!response.ok) {
      throw new Error('Failed to fetch top countries');
    }
    
    const data = await response.json();
    cachedTopCountries = data;
    return data;
  } catch (error) {
    console.error('Error fetching top countries:', error);
    return [];
  }
};

export const getDailyAverages = async (): Promise<DailyAverageResponse> => {
  try {
    const response = await fetch('/api/v1/articles/daily-averages');
    if (!response.ok) {
      throw new Error('Failed to fetch daily averages');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching daily averages:', error);
    return {
      highest: [],
      lowest: []
    };
  }
};
