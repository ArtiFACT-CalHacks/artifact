import { NewsData, Article } from '@/types/article';

const AGENT_ENDPOINT = 'https://agents.toolhouse.ai/949d9de0-1bb0-499e-bc57-f64c7edeeec3';
const CACHE_KEY = 'toolhouse_news_cache';
const CACHE_DURATION = 3600000; // 1 hour in milliseconds
const REQUEST_TIMEOUT = 90000; // 90 seconds
const POLL_INTERVAL = 3000; // Poll every 3 seconds
const MAX_POLLS = 20; // Max 20 polls (60 seconds total)

interface CachedData {
  articles: Article[];
  timestamp: number;
}

const pollForResults = async (runId: string, pollCount: number = 0): Promise<string> => {
  if (pollCount >= MAX_POLLS) {
    throw new Error('Agent took too long to respond. Please try again.');
  }

  console.log(`🔄 Polling for results (attempt ${pollCount + 1}/${MAX_POLLS})...`);
  
  // Wait before polling
  await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
  
  try {
    const response = await fetch(`${AGENT_ENDPOINT}/runs/${runId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      console.log('⚠️ Poll response not ready yet, will retry...');
      return pollForResults(runId, pollCount + 1);
    }

    const text = await response.text();
    
    if (!text || text.trim().length === 0) {
      console.log('⚠️ Empty response, polling again...');
      return pollForResults(runId, pollCount + 1);
    }

    console.log('✅ Got results from polling!');
    return text;
    
  } catch (error) {
    console.log('⚠️ Poll failed, retrying...', error);
    return pollForResults(runId, pollCount + 1);
  }
};

export const fetchNewsFromToolhouse = async (): Promise<NewsData> => {
  try {
    console.log('🔄 Fetching from Toolhouse agent...');
    console.log('📍 Endpoint:', AGENT_ENDPOINT);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    
    try {
      const response = await fetch(AGENT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [{
            role: 'user',
            content: 'Find and summarize 10 recent, credible news articles covering AI-generated media — including both positive innovations and negative incidents. Return results in JSON format with fields: title, summary, type, source, date, ai_involvement (array), impact, and url.'
          }]
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      
      console.log('📡 Response status:', response.status);
      
      // Get the run ID from headers
      const runId = response.headers.get('x-toolhouse-run-id');
      console.log('🆔 Run ID:', runId);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`Agent request failed: ${response.status}`);
      }

      // Get initial response
      const textResponse = await response.text();
      console.log('📄 Initial response length:', textResponse.length);
      console.log('📄 Initial response (first 500 chars):', textResponse.substring(0, 500));
      
      let content = textResponse;
      
      // If response is empty and we have a run ID, poll for results
      if ((!content || content.trim().length === 0) && runId) {
        console.log('⏳ Response empty, polling for results...');
        content = await pollForResults(runId);
      }
      
      if (!content || content.trim().length === 0) {
        throw new Error('Agent returned empty response. Please try again.');
      }
      
      // Try to parse the response
      let data;
      try {
        data = JSON.parse(content);
        console.log('✅ Successfully parsed as JSON');
      } catch (parseError) {
        console.log('⚠️ Not valid JSON, extracting...');
        
        // Try to extract JSON from markdown code blocks
        const codeBlockMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
        if (codeBlockMatch) {
          console.log('✅ Found JSON in code block');
          data = JSON.parse(codeBlockMatch[1]);
        } else {
          // Try to find JSON object
          const jsonMatch = content.match(/\{[\s\S]*"articles"[\s\S]*\}/);
          if (jsonMatch) {
            console.log('✅ Found JSON object');
            data = JSON.parse(jsonMatch[0]);
          } else {
            throw new Error('Could not extract JSON from response');
          }
        }
      }
      
      // Extract articles from various possible formats
      let articles: Article[] = [];
      
      if (Array.isArray(data)) {
        articles = data;
      } else if (data.articles && Array.isArray(data.articles)) {
        articles = data.articles;
      } else if (data.content) {
        // Try parsing content field
        try {
          const contentData = JSON.parse(data.content);
          articles = contentData.articles || [];
        } catch {
          throw new Error('Could not find articles in response');
        }
      } else {
        throw new Error('Response does not contain articles array');
      }
      
      if (articles.length === 0) {
        throw new Error('No articles found in response');
      }
      
      console.log('✅ Parsed articles:', articles.length);
      
      const newsData: NewsData = { articles };
      
      // Cache the results
      const cacheData: CachedData = {
        articles: newsData.articles,
        timestamp: Date.now()
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));

      return newsData;
      
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      
      if (fetchError.name === 'AbortError') {
        console.error('⏱️ Request timed out');
        throw new Error('Request timed out. Please try again.');
      }
      
      throw fetchError;
    }
    
  } catch (error: any) {
    console.error('❌ Error fetching from Toolhouse:', error);
    throw error;
  }
};

export const getCachedNews = (): NewsData | null => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const data: CachedData = JSON.parse(cached);
    const age = Date.now() - data.timestamp;

    if (age < CACHE_DURATION) {
      return { articles: data.articles };
    }

    return null;
  } catch (error) {
    console.error('Error reading cache:', error);
    return null;
  }
};

export const getCacheAge = (): string | null => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const data: CachedData = JSON.parse(cached);
    const ageMinutes = Math.floor((Date.now() - data.timestamp) / 60000);

    if (ageMinutes < 60) {
      return `${ageMinutes} minute${ageMinutes !== 1 ? 's' : ''} ago`;
    }

    const ageHours = Math.floor(ageMinutes / 60);
    return `${ageHours} hour${ageHours !== 1 ? 's' : ''} ago`;
  } catch {
    return null;
  }
};