import { AnalysisResult } from '@/types/analysis';

const STORAGE_KEY = 'artifact_analysis_history';
const MAX_HISTORY_ITEMS = 100;

export const getHistory = (): AnalysisResult[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error reading history:', error);
    return [];
  }
};

export const addToHistory = (analysis: AnalysisResult): void => {
  try {
    const history = getHistory();
    const updated = [analysis, ...history].slice(0, MAX_HISTORY_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Error saving to history:', error);
  }
};

export const deleteFromHistory = (id: string): void => {
  try {
    const history = getHistory();
    const updated = history.filter(item => item.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Error deleting from history:', error);
  }
};

export const clearHistory = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing history:', error);
  }
};