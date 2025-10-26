import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Trash2, ArrowUpDown, Download } from 'lucide-react';
import { Input } from '@/components/ui/input.tsx';
import { Button } from '@/components/ui/button.tsx';
import { Card } from '@/components/ui/card.tsx';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table.tsx';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog.tsx';
import { Badge } from '@/components/ui/badge.tsx';
import Navbar from '@/components/Navbar.tsx';
import Footer from '@/components/Footer.tsx';
import { getHistory, deleteFromHistory } from '@/utils/historyStorage.ts';
import { AnalysisResult } from '@/types/analysis.ts';
import { toast } from 'sonner';

type SortField = 'filename' | 'result' | 'confidence' | 'timestamp';
type SortDirection = 'asc' | 'desc';

const History = () => {
  const [history, setHistory] = useState<AnalysisResult[]>(getHistory());
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const filteredAndSortedHistory = useMemo(() => {
    let filtered = history.filter(item =>
      item.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );

    filtered.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'timestamp') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      } else if (sortField === 'confidence') {
        aVal = a.confidence;
        bVal = b.confidence;
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [history, searchTerm, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleDelete = (id: string) => {
    deleteFromHistory(id);
    setHistory(getHistory());
    setDeleteId(null);
    toast.success('Analysis deleted from history');
  };

  const handleExportHistory = () => {
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `artifact-history-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('History exported successfully');
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-white text-[#4a2400] flex flex-col">
      <Navbar />
      
      <main className="flex-1 pt-24 pb-8">
        <div className="container mx-auto px-4 max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold text-[#2D44C8] mb-2 font-serif">Analysis History</h1>
                <p className="text-black/70">View and manage your past authenticity checks</p>
              </div>
              {history.length > 0 && (
                <Button
                  onClick={handleExportHistory}
                  variant="outline"
                  className="border-[#2D44C8]/30 text-[#2D44C8] hover:bg-gray-50 rounded-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              )}
            </div>

            {history.length > 0 && (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-black/60 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search by filename..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white border-[#2D44C8]/30 text-black rounded-full"
                />
              </div>
            )}
          </motion.div>

          {history.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <Card className="p-12 text-center bg-white border-[#2D44C8]/30 shadow-md">
                <div className="text-black/70 mb-4">
                  <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-xl font-semibold text-[#000000] mb-2 font-serif">No analyses yet</h3>
                  <p>Upload and analyze media files to see your history here</p>
                </div>
                <Button
                  onClick={() => window.location.href = '/detect'}
                  className="mt-4 bg-[#2D44C8] hover:bg-[#1F2E8A] text-white rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)]"
                >
                  Start Analyzing
                </Button>
              </Card>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <Card className="bg-white border-[#2D44C8]/30 overflow-hidden shadow-md">
                <Table>
                  <TableHeader>
                    <TableRow className="border-[#2D44C8]/20 hover:bg-gray-50">
                      <TableHead 
                        className="text-black/70 cursor-pointer hover:text-[#2D44C8]"
                        onClick={() => handleSort('filename')}
                      >
                        <div className="flex items-center gap-2">
                          Filename
                          <ArrowUpDown className="w-4 h-4" />
                        </div>
                      </TableHead>
                      <TableHead 
                        className="text-black/70 cursor-pointer hover:text-[#2D44C8]"
                        onClick={() => handleSort('result')}
                      >
                        <div className="flex items-center gap-2">
                          Result
                          <ArrowUpDown className="w-4 h-4" />
                        </div>
                      </TableHead>
                      <TableHead 
                        className="text-black/70 cursor-pointer hover:text-[#2D44C8]"
                        onClick={() => handleSort('confidence')}
                      >
                        <div className="flex items-center gap-2">
                          Confidence
                          <ArrowUpDown className="w-4 h-4" />
                        </div>
                      </TableHead>
                      <TableHead 
                        className="text-black/70 cursor-pointer hover:text-[#2D44C8]"
                        onClick={() => handleSort('timestamp')}
                      >
                        <div className="flex items-center gap-2">
                          Date
                          <ArrowUpDown className="w-4 h-4" />
                        </div>
                      </TableHead>
                      <TableHead className="text-black/70">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredAndSortedHistory.map((item) => (
                      <TableRow 
                        key={item.id}
                        className="border-[#2D44C8]/20 hover:bg-gray-50"
                      >
                        <TableCell className="text-black font-medium">
                          {item.filename}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={item.result === 'AI' ? 'destructive' : 'default'}
                            className={item.result === 'AI' ? 'bg-red-500/20 text-red-600 border-red-500/50' : 'bg-green-500/20 text-green-600 border-green-500/50'}
                          >
                            {item.result}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-black">
                          {Math.round(item.confidence * 100)}%
                        </TableCell>
                        <TableCell className="text-black/70">
                          {formatDate(item.timestamp)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(item.id)}
                            className="text-black/60 hover:text-red-600 hover:bg-red-500/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>

              {filteredAndSortedHistory.length === 0 && searchTerm && (
                <div className="text-center py-8 text-black/70">
                  No results found for "{searchTerm}"
                </div>
              )}
            </motion.div>
          )}
        </div>
      </main>

      <Footer />

      <AlertDialog open={deleteId !== null} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent className="bg-white border-[#2D44C8]/30">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-[#2D44C8] font-serif">Delete Analysis</AlertDialogTitle>
            <AlertDialogDescription className="text-black/70">
              Are you sure you want to delete this analysis record? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-50 text-black border-[#2D44C8]/30 hover:bg-gray-100 rounded-full">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteId && handleDelete(deleteId)}
              className="bg-red-600 hover:bg-red-700 text-white rounded-full"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default History;