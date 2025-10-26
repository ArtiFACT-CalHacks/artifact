export interface Article {
  title: string;
  summary: string;
  type: string;
  source: string;
  date: string;
  ai_involvement: string[];
  impact: string;
  url: string;
}

export interface NewsData {
  articles: Article[];
}