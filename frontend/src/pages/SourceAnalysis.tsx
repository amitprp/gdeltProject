import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2, ExternalLink } from "lucide-react";
import {
  getGroupedSources,
  getSourceAnalysis,
  GroupedSourceData,
  SourceAnalysisData,
  SourceAnalysisFilters
} from "@/services/dataService";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import BackToHome from "@/components/BackToHome";
import { CountrySelect } from "@/components/CountrySelect";
import { getCountryCode } from "@/lib/countries";
import { ExportButton } from "@/components/ExportButton";

const SourceAnalysis = () => {
  console.log('Component rendering');
  
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<"author" | "country">("author");
  const [searchTerm, setSearchTerm] = useState("");
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();
  const [apiResults, setApiResults] = useState<GroupedSourceData[]>([]);
  const [displayedSources, setDisplayedSources] = useState<GroupedSourceData[]>([]);
  const tableRef = useRef<HTMLDivElement>(null);

  const fetchSources = async () => {
    setLoading(true);
    try {
      console.log('fetchSources called with:', { searchTerm, filterType, startDate, endDate });
      
      if (searchTerm) {
        const filters: SourceAnalysisFilters = {
          startDate,
          endDate,
          ...(filterType === "author" 
            ? { author: searchTerm } 
            : { country: getCountryCode(searchTerm) || searchTerm }
          )
        };
        
        console.log('Fetching source analysis with filters:', filters);
        const data = await getSourceAnalysis(filters);
        console.log('Received source analysis data:', data);
        
        const convertedData: GroupedSourceData[] = data.map(item => ({
          name: filterType === "author" ? item.source : item.country,
          articleCount: item.articleCount,
          averageTone: item.averageTone,
          lastArticleDate: item.lastArticleDate,
          recentArticles: item.recentArticles
        }));
        
        console.log('Setting sources with converted data:', convertedData);
        setApiResults(convertedData);
        setDisplayedSources(convertedData);
      } else {
        console.log('Fetching grouped sources');
        const data = await getGroupedSources(filterType, startDate, endDate);
        console.log('Received grouped sources data:', data);
        setApiResults(data);
        setDisplayedSources(data);
      }
    } catch (error) {
      console.error('Error in fetchSources:', error);
    }
    setLoading(false);
  };

  // Handle local filtering of results
  const handleSearchFilter = (term: string) => {
    setSearchTerm(term);
    if (!term) {
      setDisplayedSources(apiResults);
    } else {
      const filtered = apiResults.filter(source =>
        source.name.toLowerCase().includes(term.toLowerCase())
      );
      setDisplayedSources(filtered);
    }
  };

  const handleFilter = () => {
    console.log('Handle filter clicked');
    fetchSources();
  };

  // Transform data for Excel export
  const getExportData = () => {
    return displayedSources.map(source => ({
      [filterType === "author" ? "Author" : "Country"]: source.name,
      "Article Count": source.articleCount,
      "Average Tone": source.averageTone.toFixed(2),
      "Last Article Date": new Date(source.lastArticleDate).toLocaleDateString(),
      "Recent Articles": source.recentArticles.map(article => article.title).join(", ")
    }));
  };

  // Add cleanup logging
  useEffect(() => {
    return () => {
      console.log('Component unmounting');
    };
  }, []);

  return (
    <div className="container mx-auto py-8 px-4">
      <BackToHome />
      <h1 className="text-3xl font-bold mb-8">Source Analysis</h1>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Filter Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Group By</label>
              <Select
                value={filterType}
                onValueChange={(value: "author" | "country") => {
                  setFilterType(value);
                  setSearchTerm("");
                  setDisplayedSources(apiResults);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="author">Author</SelectItem>
                  <SelectItem value="country">Country</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Search {filterType === "author" ? "Author" : "Country"}
              </label>
              {filterType === "country" ? (
                <CountrySelect
                  value={searchTerm}
                  onChange={(name) => {
                    setSearchTerm(name);
                    setDisplayedSources(apiResults);
                  }}
                />
              ) : (
                <Input
                  placeholder="Search by author"
                  value={searchTerm}
                  onChange={(e) => handleSearchFilter(e.target.value)}
                />
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <DatePicker date={startDate} setDate={setStartDate} />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <DatePicker date={endDate} setDate={setEndDate} />
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleFilter} disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Results</CardTitle>
          {displayedSources.length > 0 && !loading && (
            <ExportButton
              targetRef={tableRef}
              type="table"
              data={getExportData()}
              filename="source-analysis-results"
            />
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : displayedSources.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchTerm ? (
                <p>No results found for {filterType === "country" ? "country" : "author"}: {searchTerm}</p>
              ) : (
                <p>No data available. Try adjusting your filters or search terms.</p>
              )}
            </div>
          ) : (
            <div ref={tableRef}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{filterType === "author" ? "Author" : "Country"}</TableHead>
                    <TableHead className="text-right">Article Count</TableHead>
                    <TableHead className="text-right">Average Tone</TableHead>
                    <TableHead>Last Article</TableHead>
                    <TableHead>Recent Articles</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedSources.map((source, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{source.name}</TableCell>
                      <TableCell className="text-right">{source.articleCount}</TableCell>
                      <TableCell className="text-right">
                        {source.averageTone.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        {new Date(source.lastArticleDate).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Accordion type="single" collapsible>
                          <AccordionItem value="articles">
                            <AccordionTrigger>
                              View Recent Articles ({source.recentArticles.length})
                            </AccordionTrigger>
                            <AccordionContent>
                              <div className="space-y-2">
                                {source.recentArticles.map((article, idx) => (
                                  <div key={idx} className="flex items-start space-x-2 text-sm">
                                    <div className="flex-1">
                                      <a
                                        href={article.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-500 hover:underline flex items-center"
                                      >
                                        {article.title}
                                        <ExternalLink className="h-3 w-3 ml-1" />
                                      </a>
                                      <div className="text-gray-500">
                                        {new Date(article.date).toLocaleDateString()} |
                                        Tone: {article.tone.toFixed(2)}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SourceAnalysis; 