export interface GroupedSourceData {
  name: string;
  code?: string;  // Country code for country grouping
  articleCount: number;
  averageTone: number;
  lastArticleDate: string;
  recentArticles: RecentArticle[];
}

export interface RecentArticle {
  title: string;
  url: string;
  date: string;
  tone: number;
} 