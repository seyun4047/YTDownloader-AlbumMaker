import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Music, 
  Video, 
  Headphones, 
  Link as LinkIcon, 
  Settings2, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  History,
  Trash2,
  ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

// --- Constants & Types ---
const API_BASE_URL = '/api';

type DownloadMode = 'audio' | 'video' | 'music';
type Quality = 'low' | 'middle' | 'high' | 'max' | string;

interface DownloadItem {
  id: string;
  url: string;
  mode: DownloadMode;
  quality: Quality;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  timestamp: number;
  fileName?: string;
  downloadUrl?: string;
  error?: string;
}

const QUALITY_OPTIONS: { value: Quality; label: string; audio: string; video: string }[] = [
  { value: 'low', label: 'Low', audio: '128 kbps', video: '480p' },
  { value: 'middle', label: 'Middle', audio: '192 kbps', video: '720p' },
  { value: 'high', label: 'High', audio: '256 kbps', video: '1080p' },
  { value: 'max', label: 'Max', audio: '320 kbps', video: '4K' },
];

export default function App() {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<DownloadMode>('audio');
  const [quality, setQuality] = useState<Quality>('high');
  const [musicOptions, setMusicOptions] = useState({ lyric: false, metadata: false });
  const [history, setHistory] = useState<DownloadItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('yt_download_history');
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  // Save history to localStorage
  useEffect(() => {
    localStorage.setItem('yt_download_history', JSON.stringify(history));
  }, [history]);

  const processDownload = async (targetUrl: string, id: string, currentMode: DownloadMode = mode, currentMusicOptions = musicOptions, bypassAutoDownload = false) => {
    try {
      setHistory(prev => prev.map(item => item.id === id ? { ...item, status: 'downloading' } : item));

      let endpoint = `/yt/${currentMode}`;
      let body: any = { url: targetUrl, quality };

      if (currentMode === 'music') {
        body = { ...body, ...currentMusicOptions };
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) throw new Error(`Server responded with ${response.status}`);

      const data = await response.json();
      
      const downloadUrl = data.url.startsWith('http') ? data.url : `${API_BASE_URL}${data.url}`;
      const fileName = downloadUrl.split('/').pop() || 'download';

      setHistory(prev => prev.map(item => 
        item.id === id ? { ...item, status: 'completed', downloadUrl, fileName } : item
      ));

      // Automatically trigger download
      if (!bypassAutoDownload) {
        window.open(downloadUrl, '_blank');
      } else {
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.target = '_blank';
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (err: any) {
      setHistory(prev => prev.map(item => 
        item.id === id ? { ...item, status: 'error', error: err.message } : item
      ));
    }
  };

  const handleDownload = async () => {
    if (!url.trim()) return;

    const targetUrl = url;
    setUrl(''); // Clear input

    if (targetUrl.includes('list=')) {
      setIsProcessing(true);
      try {
        const response = await fetch(`${API_BASE_URL}/yt/playlist`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: targetUrl, quality })
        });
        if (!response.ok) throw new Error('Failed to fetch playlist links');
        
        const data = await response.json();
        const urls: string[] = data.urls;

        if (urls && urls.length > 0) {
          const newItems = urls.map(u => ({
            id: Math.random().toString(36).substring(7),
            url: u,
            mode,
            quality,
            status: 'pending' as const,
            timestamp: Date.now(),
          }));
          setHistory(prev => [...newItems, ...prev]);

          // Process each one completely sequentially
          for (const item of newItems) {
            await processDownload(item.url, item.id, mode, musicOptions, true);
          }
        } else {
          throw new Error('No videos found in playlist');
        }
      } catch (err: any) {
         // Show error message for playlist fetch failure
         alert('Failed to process playlist: ' + err.message);
      } finally {
        setIsProcessing(false);
      }
    } else {
      const id = Math.random().toString(36).substring(7);
      const newItem: DownloadItem = {
        id,
        url: targetUrl,
        mode,
        quality,
        status: 'pending',
        timestamp: Date.now(),
      };
      setHistory(prev => [newItem, ...prev]);
      setIsProcessing(true);
      await processDownload(targetUrl, id);
      setIsProcessing(false);
    }
  };

  const removeHistoryItem = (id: string) => {
    setHistory(prev => prev.filter(item => item.id !== id));
  };

  const clearHistory = () => {
    if (confirm('Clear all history?')) {
      setHistory([]);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-zinc-300 font-sans selection:bg-emerald-500/30">
      {/* Background Decorative Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-emerald-500/5 blur-[120px] rounded-full" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-blue-500/5 blur-[120px] rounded-full" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay" />
      </div>

      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12 lg:py-20">
        {/* Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 mb-2"
            >
              <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <Download className="w-6 h-6 text-emerald-400" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white">
                MUTZIN <span className="text-emerald-400">YT</span>
              </h1>
            </motion.div>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-zinc-500 text-sm max-w-md"
            >
              High-performance media extraction tool. 
              Supports 4K video, 320kbps audio, and metadata embedding.
            </motion.p>
          </div>
          
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-4 text-[10px] font-mono uppercase tracking-widest text-zinc-600"
          >
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Online
            </div>
            <div className="w-px h-4 bg-zinc-800" />
            <div>Port: 10211</div>
            <div className="w-px h-4 bg-zinc-800" />
            <div>API: 10210</div>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Controls */}
          <div className="lg:col-span-7 space-y-6">
            {/* URL Input Card */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-zinc-900/50 border border-zinc-800/50 rounded-2xl p-6 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex items-center gap-2 mb-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                <LinkIcon className="w-3.5 h-3.5" />
                Target URL
              </div>
              <div className="relative group">
                <input 
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste YouTube link here..."
                  className="w-full bg-black/40 border border-zinc-800 rounded-xl px-4 py-4 text-white placeholder:text-zinc-700 focus:outline-none focus:border-emerald-500/50 transition-all group-hover:border-zinc-700"
                />
                <div className="absolute inset-0 rounded-xl bg-emerald-500/5 opacity-0 group-focus-within:opacity-100 pointer-events-none transition-opacity" />
              </div>
            </motion.div>

            {/* Configuration Card */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-zinc-900/50 border border-zinc-800/50 rounded-2xl p-6 backdrop-blur-xl"
            >
              <div className="flex items-center gap-2 mb-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                <Settings2 className="w-3.5 h-3.5" />
                Extraction Parameters
              </div>

              <div className="space-y-8">
                {/* Mode Selector */}
                <div>
                  <label className="text-xs text-zinc-500 mb-3 block">Output Format</label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['audio', 'video', 'music'] as DownloadMode[]).map((m) => (
                      <button
                        key={m}
                        onClick={() => setMode(m)}
                        className={`
                          flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all
                          ${mode === m 
                            ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]' 
                            : 'bg-black/20 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-400'}
                        `}
                      >
                        {m === 'audio' && <Headphones className="w-5 h-5" />}
                        {m === 'video' && <Video className="w-5 h-5" />}
                        {m === 'music' && <Music className="w-5 h-5" />}
                        <span className="text-[10px] font-bold uppercase tracking-tighter">{m}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Quality Selector */}
                <div>
                  <label className="text-xs text-zinc-500 mb-3 block">Quality Profile</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {QUALITY_OPTIONS.map((q) => (
                      <button
                        key={q.value}
                        onClick={() => setQuality(q.value)}
                        className={`
                          flex flex-col p-3 rounded-lg border text-left transition-all
                          ${quality === q.value 
                            ? 'bg-zinc-800 border-zinc-600 text-white' 
                            : 'bg-black/20 border-zinc-800/50 text-zinc-600 hover:border-zinc-700'}
                        `}
                      >
                        <span className="text-[10px] font-bold uppercase mb-1">{q.label}</span>
                        <span className="text-[9px] opacity-60 font-mono">
                          {mode === 'video' ? q.video : q.audio}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Music Specific Options */}
                <AnimatePresence>
                  {mode === 'music' && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="pt-4 border-t border-zinc-800/50"
                    >
                      <label className="text-xs text-zinc-500 mb-3 block">Music Metadata</label>
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <input 
                            type="checkbox" 
                            checked={musicOptions.lyric}
                            onChange={(e) => setMusicOptions(prev => ({ ...prev, lyric: e.target.checked }))}
                            className="hidden"
                          />
                          <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${musicOptions.lyric ? 'bg-emerald-500 border-emerald-500' : 'border-zinc-700 group-hover:border-zinc-500'}`}>
                            {musicOptions.lyric && <CheckCircle2 className="w-3 h-3 text-black" />}
                          </div>
                          <span className="text-xs text-zinc-400">Embed Lyrics</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer group">
                          <input 
                            type="checkbox" 
                            checked={musicOptions.metadata}
                            onChange={(e) => setMusicOptions(prev => ({ ...prev, metadata: e.target.checked }))}
                            className="hidden"
                          />
                          <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${musicOptions.metadata ? 'bg-emerald-500 border-emerald-500' : 'border-zinc-700 group-hover:border-zinc-500'}`}>
                            {musicOptions.metadata && <CheckCircle2 className="w-3 h-3 text-black" />}
                          </div>
                          <span className="text-xs text-zinc-400">Make Album</span>
                        </label>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Action Button */}
              <button
                onClick={handleDownload}
                disabled={isProcessing || !url.trim()}
                className={`
                  w-full mt-8 py-4 rounded-xl font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all
                  ${isProcessing || !url.trim()
                    ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
                    : 'bg-emerald-500 text-black hover:bg-emerald-400 active:scale-[0.98] shadow-[0_0_30px_rgba(16,185,129,0.2)]'}
                `}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    Initialize Download
                  </>
                )}
              </button>
            </motion.div>
          </div>

          {/* Right Column: History */}
          <div className="lg:col-span-5 flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                <History className="w-3.5 h-3.5" />
                Session History
              </div>
              {history.length > 0 && (
                <button 
                  onClick={clearHistory}
                  className="text-[10px] text-zinc-600 hover:text-red-400 transition-colors flex items-center gap-1"
                >
                  <Trash2 className="w-3 h-3" />
                  Clear
                </button>
              )}
            </div>

            <div className="flex-1 bg-zinc-900/30 border border-zinc-800/50 rounded-2xl overflow-hidden flex flex-col min-h-[400px]">
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                <AnimatePresence initial={false}>
                  {history.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-700 space-y-2 opacity-50">
                      <History className="w-8 h-8" />
                      <p className="text-xs font-medium">No active downloads</p>
                    </div>
                  ) : (
                    history.map((item) => (
                      <motion.div
                        key={item.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="bg-black/40 border border-zinc-800/50 rounded-xl p-4 group"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              {item.mode === 'audio' && <Headphones className="w-3 h-3 text-blue-400" />}
                              {item.mode === 'video' && <Video className="w-3 h-3 text-purple-400" />}
                              {item.mode === 'music' && <Music className="w-3 h-3 text-emerald-400" />}
                              <span className="text-[10px] font-mono text-zinc-500 truncate">
                                {item.url}
                              </span>
                            </div>
                            <h3 className="text-xs font-medium text-zinc-300 truncate mb-2">
                              {item.fileName || 'Processing media...'}
                            </h3>
                            
                            <div className="flex items-center gap-3">
                              <div className={`
                                px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-tighter
                                ${item.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 
                                  item.status === 'error' ? 'bg-red-500/10 text-red-400' : 
                                  'bg-blue-500/10 text-blue-400 animate-pulse'}
                              `}>
                                {item.status}
                              </div>
                              <span className="text-[9px] text-zinc-600 font-mono">
                                {item.quality} • {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                          </div>

                          <div className="flex flex-col gap-2">
                            {item.status === 'completed' && item.downloadUrl && (
                              <a 
                                href={item.downloadUrl} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg hover:bg-emerald-500 hover:text-black transition-all"
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                            <button 
                              onClick={() => removeHistoryItem(item.id)}
                              className="p-2 text-zinc-700 hover:text-red-400 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {item.status === 'error' && (
                          <div className="mt-3 pt-3 border-t border-red-500/10 flex items-center gap-2 text-[9px] text-red-400/80">
                            <AlertCircle className="w-3 h-3" />
                            {item.error}
                          </div>
                        )}
                      </motion.div>
                    ))
                  )}
                </AnimatePresence>
              </div>
              
              {/* Footer Stats */}
              <div className="p-4 bg-black/40 border-t border-zinc-800/50 flex items-center justify-between text-[9px] font-mono text-zinc-600 uppercase tracking-widest">
                <span>Total: {history.length}</span>
                <span>Active: {history.filter(h => h.status === 'downloading').length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <footer className="mt-20 pt-8 border-t border-zinc-900 flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] text-zinc-600 font-mono uppercase tracking-widest">
          <div className="flex items-center gap-6">
            <span className="hover:text-zinc-400 cursor-help transition-colors">Documentation</span>
            <span className="hover:text-zinc-400 cursor-help transition-colors">API Status</span>
            <span className="hover:text-zinc-400 cursor-help transition-colors">Privacy</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-zinc-800" />
            MUTZIN@MUTZIN.COM
          </div>
        </footer>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #27272a;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #3f3f46;
        }
      `}} />
    </div>
  );
}
