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
import { Loader2, ExternalLink, X } from "lucide-react";
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
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import BackToHome from "@/components/BackToHome";
import { CountrySelect } from "@/components/CountrySelect";
import { getCountryCode } from "@/lib/countries";
import { ExportButton } from "@/components/ExportButton";

const ITEMS_PER_PAGE = 8;

const SourceAnalysis = () => {
  console.log('Component rendering');
  
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<"author" | "country">("author");
  const [activeFilterType, setActiveFilterType] = useState<"author" | "country">("author");
  const [searchTerm, setSearchTerm] = useState("");
  const [pendingSearchTerm, setPendingSearchTerm] = useState("");
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();
  const [apiResults, setApiResults] = useState<GroupedSourceData[]>([]);
  const [displayedSources, setDisplayedSources] = useState<GroupedSourceData[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const tableRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string>();

  // Calculate pagination values
  const totalItems = displayedSources.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentItems = displayedSources.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const fetchSources = async () => {
    try {
      console.log('fetchSources called with:', { 
        pendingSearchTerm,
        filterType, 
        startDate, 
        endDate 
      });
      setError("");
      const now = new Date();
      if (startDate && endDate && startDate > endDate) {
        setError("Start date must be before end date");
        setLoading(false);
        return;
      }

      if ((startDate && startDate > now) || endDate && endDate > now) {
        setError("Dates cannot be in the future");
        setLoading(false);
        return;
      }
      setLoading(true);
      
      if ((filterType === "country" && pendingSearchTerm) || 
          (filterType === "author" && pendingSearchTerm)) {
            
        const filters: SourceAnalysisFilters = {
          startDate,
          endDate,
          ...(filterType === "author" 
            ? { author: pendingSearchTerm.toLowerCase() }
            : { country: getCountryCode(pendingSearchTerm) || pendingSearchTerm }
          )
        };
        
        console.log('Fetching source analysis with filters:', filters);
        const data = await getSourceAnalysis(filters);
        console.log('Received source analysis data:', data);
        
        // Ensure unique articles by title
        const uniqueArticles = new Map();
        const convertedData: GroupedSourceData[] = data.map(item => {
          // Filter out duplicate articles
          const uniqueRecentArticles = item.recentArticles.filter(article => {
            if (uniqueArticles.has(article.title)) {
              return false;
            }
            uniqueArticles.set(article.title, true);
            return true;
          });

          return {
            name: filterType === "author" ? item.source || "Unknown" : item.country || "Unknown",
            source: item.source || item.pageAuthors,
            articleCount: item.articleCount,
            averageTone: item.averageTone,
            lastArticleDate: item.lastArticleDate,
            recentArticles: uniqueRecentArticles
          };
        });
        
        console.log('Setting sources with converted data:', convertedData);
        setApiResults(convertedData);
        setDisplayedSources(convertedData);
      } else {
        console.log('Fetching grouped sources');
        const data = await getGroupedSources(filterType, startDate, endDate);
        console.log('Received grouped sources data:', data);
        
        // Ensure unique articles by title
        const uniqueArticles = new Map();
        const processedData = data.map(item => {
          // Filter out duplicate articles
          const uniqueRecentArticles = item.recentArticles.filter(article => {
            if (uniqueArticles.has(article.title)) {
              return false;
            }
            uniqueArticles.set(article.title, true);
            return true;
          });

          return {
            ...item,
            recentArticles: uniqueRecentArticles
          };
        });
        
        setApiResults(processedData);
        setDisplayedSources(processedData);
      }
    } catch (error) {
      console.error('Error in fetchSources:', error);
    }
    setLoading(false);
  };

  const handleSearchFilter = (term: string) => {
    if (filterType === "author") {
      // For author search, keep the existing behavior of immediate filtering
      setPendingSearchTerm(term);
      setCurrentPage(1);
      if (!term) {
        setDisplayedSources(apiResults);
      } else {
        const searchLower = term.toLowerCase();
        const filtered = apiResults.filter(source =>
          source.name.toLowerCase().includes(searchLower)
        );
        setDisplayedSources(filtered);
      }
    } else {
      // For country search, only update the pending term
      setPendingSearchTerm(term);
    }
  };

  const handleFilter = () => {
    console.log('Handle filter clicked');
    setCurrentPage(1);
    setActiveFilterType(filterType);

    setSearchTerm(pendingSearchTerm);
    
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
                  setPendingSearchTerm("");
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
                <div className="flex gap-2">
                  <CountrySelect
                    value={pendingSearchTerm}
                    onChange={(name) => {
                      handleSearchFilter(name);
                    }}
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      setPendingSearchTerm("");
                      setSearchTerm("");
                      handleFilter();
                    }}
                    title="Reset country search"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Input
                    placeholder="Search by author"
                    value={pendingSearchTerm}
                    onChange={(e) => handleSearchFilter(e.target.value)}
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      setPendingSearchTerm("");
                      setSearchTerm("");
                      handleFilter();
                    }}
                    title="Reset author search"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <div className="flex gap-2">
                <DatePicker date={startDate} setDate={setStartDate} />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setStartDate(undefined)}
                  title="Reset start date"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <div className="flex gap-2">
                <DatePicker date={endDate} setDate={setEndDate} />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setEndDate(undefined)}
                  title="Reset end date"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
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
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-500">{error}</p>
            </div>
          ) : displayedSources.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchTerm ? (
                <p>No results found for {activeFilterType === "country" ? "country" : "author"}: {searchTerm}</p>
              ) : (
                <p>No data available. Try adjusting your filters or search terms.</p>
              )}
            </div>
          ) : (
            <>
              <div ref={tableRef}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{activeFilterType === "author" ? "Author" : "Country"}</TableHead>
                      {activeFilterType === "country" && searchTerm && (
                        <TableHead>Author</TableHead>
                      )}
                      <TableHead className="text-right">Article Count</TableHead>
                      <TableHead className="text-right">Average Tone</TableHead>
                      <TableHead>Last Article</TableHead>
                      <TableHead>Recent Articles</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentItems.map((source, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{source.name}</TableCell>
                        {activeFilterType === "country" && searchTerm && (
                          <TableCell>{source.source || "Unknown"}</TableCell>
                        )}
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
              {totalPages > 1 && (
                <div className="mt-4">
                  <Pagination>
                    <PaginationContent>
                      {currentPage > 1 && (
                        <PaginationItem>
                          <PaginationPrevious onClick={() => handlePageChange(currentPage - 1)} />
                        </PaginationItem>
                      )}
                      
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        if (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1)
                        ) {
                          return (
                            <PaginationItem key={page}>
                              <PaginationLink
                                isActive={page === currentPage}
                                onClick={() => handlePageChange(page)}
                              >
                                {page}
                              </PaginationLink>
                            </PaginationItem>
                          );
                        } else if (
                          page === currentPage - 2 ||
                          page === currentPage + 2
                        ) {
                          return (
                            <PaginationItem key={page}>
                              <PaginationEllipsis />
                            </PaginationItem>
                          );
                        }
                        return null;
                      })}
                      
                      {currentPage < totalPages && (
                        <PaginationItem>
                          <PaginationNext onClick={() => handlePageChange(currentPage + 1)} />
                        </PaginationItem>
                      )}
                    </PaginationContent>
                  </Pagination>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SourceAnalysis; 