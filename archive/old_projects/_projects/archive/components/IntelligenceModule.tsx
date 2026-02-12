
import React, { useState, useRef, useEffect } from 'react';
import { gemini } from '../services/geminiService';
import { AnalysisResult, ProjectState, AnalysisHistoryItem } from '../types';

interface IntelligenceModuleProps {
  onResults: (res: AnalysisResult) => void;
  projectMetadata: ProjectState;
  onUpdateMetadata: (metadata: ProjectState) => void;
}

const STEPS = [
  "Initializing synthesis engine...",
  "Executing deep architectural scan...",
  "Performing real-time market intelligence tracking...",
  "Grounding industry data via Google Search...",
  "Finalizing studio artifacts..."
];

const IntelligenceModule: React.FC<IntelligenceModuleProps> = ({ onResults, projectMetadata, onUpdateMetadata }) => {
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isListening, setIsListening] = useState<null | 'command' | 'name' | 'description'>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const savedHistory = localStorage.getItem('stratagem_history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  const saveHistory = (newHistory: AnalysisHistoryItem[]) => {
    setHistory(newHistory);
    localStorage.setItem('stratagem_history', JSON.stringify(newHistory.slice(0, 10)));
  };

  const handleDeepAnalysis = async () => {
    if (!projectMetadata.name || !projectMetadata.description) {
      alert("Please provide a project name and description first.");
      return;
    }
    setLoading(true);
    setCurrentStep(0);
    onUpdateMetadata({ ...projectMetadata, status: 'Analyzing' });
    
    try {
      setCurrentStep(0);
      setCurrentStep(1);
      const response = await gemini.analyzeProject(projectMetadata.name, projectMetadata.description, true);
      const parsed = JSON.parse(response.text || '{}');
      
      setCurrentStep(2);
      const searchResponse = await gemini.performMarketAnalysis(projectMetadata.name, projectMetadata.description);
      const marketText = searchResponse.text;
      
      setCurrentStep(3);
      const mapsResponse = await gemini.findLocations(`${projectMetadata.name} supply chain and industry hubs`);
      
      const webSources = searchResponse.candidates?.[0]?.groundingMetadata?.groundingChunks || [];
      const mapsSources = mapsResponse.candidates?.[0]?.groundingMetadata?.groundingChunks || [];

      setCurrentStep(4);
      const result: AnalysisResult = {
        ...parsed,
        marketIntelligenceText: marketText,
        groundingSources: webSources,
        mapsSources: mapsSources
      };

      const historyItem: AnalysisHistoryItem = {
        id: crypto.randomUUID(),
        projectName: projectMetadata.name,
        status: 'Stable',
        timestamp: new Date().toLocaleString(),
        result
      };
      saveHistory([historyItem, ...history]);

      onResults(result);

    } catch (error) {
      console.error(error);
      alert("Analysis failed. Please check your API configuration.");
      onUpdateMetadata({ ...projectMetadata, status: 'Critical' });
    } finally {
      setLoading(false);
      setCurrentStep(0);
    }
  };

  const startListening = async (target: 'command' | 'name' | 'description') => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          const base64Audio = (reader.result as string).split(',')[1];
          setIsListening(null);
          
          try {
            const transcript = await gemini.transcribeAudio(base64Audio);
            
            if (target === 'command') {
              const intent = await gemini.interpretCommand(transcript);
              if (intent === 'START_ANALYSIS') {
                handleDeepAnalysis();
              } else if (intent === 'UPDATE_NAME') {
                // Heuristic: remove "change project name to"
                const cleaned = transcript.replace(/change project name to|set name to|project name is/gi, '').trim();
                onUpdateMetadata({ ...projectMetadata, name: cleaned });
              }
            } else if (target === 'name') {
              onUpdateMetadata({ ...projectMetadata, name: transcript.trim() });
            } else if (target === 'description') {
              onUpdateMetadata({ ...projectMetadata, description: transcript.trim() });
            }
          } catch (err) {
            console.error("Transcription/Intent error:", err);
          }
        };
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsListening(target);
      
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') mediaRecorder.stop();
      }, 5000);

    } catch (err) {
      console.error("Microphone access denied:", err);
      alert("Could not access microphone.");
    }
  };

  const statusOptions: ProjectState['status'][] = ['Draft', 'Analyzing', 'Stable', 'Critical'];

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8 animate-in fade-in duration-500">
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 backdrop-blur-sm relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-md z-50 flex flex-col items-center justify-center p-8 space-y-6">
            <div className="w-full max-w-md space-y-4">
              <div className="flex justify-between items-end">
                <p className="text-indigo-400 font-mono text-sm uppercase tracking-widest animate-pulse">
                  {STEPS[currentStep]}
                </p>
                <p className="text-zinc-500 text-[10px] font-bold">
                  STEP {currentStep + 1} / {STEPS.length}
                </p>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-indigo-500 h-full transition-all duration-700 ease-out shadow-[0_0_15px_rgba(99,102,241,0.5)]" 
                  style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
                />
              </div>
            </div>
            <p className="text-zinc-500 text-xs italic">Distributed architecture analysis in progress...</p>
          </div>
        )}

        <h2 className="text-2xl font-semibold mb-6">Project Configuration & Intelligence Scan</h2>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="block text-sm font-medium text-zinc-400">Project Designation</label>
                <div className="group relative">
                  <svg className="w-3.5 h-3.5 text-zinc-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="absolute left-full ml-2 top-0 w-48 p-2 bg-zinc-800 text-[10px] text-zinc-300 rounded shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                    Provide a concise unique name for the project.
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-mono"
                  placeholder="e.g. Hyperion v2"
                  value={projectMetadata.name}
                  onChange={(e) => onUpdateMetadata({ ...projectMetadata, name: e.target.value })}
                />
                <button
                  onClick={() => startListening('name')}
                  className={`px-3 bg-zinc-800 border border-zinc-700 rounded-lg hover:text-white transition-all ${isListening === 'name' ? 'text-red-500 animate-pulse border-red-500' : 'text-zinc-500'}`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Current Lifecycle Status</label>
              <div className="flex bg-zinc-950 border border-zinc-800 rounded-lg p-1 gap-1">
                {statusOptions.map((status) => (
                  <button
                    key={status}
                    onClick={() => onUpdateMetadata({ ...projectMetadata, status })}
                    className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-wider rounded-md transition-all ${
                      projectMetadata.status === status
                        ? status === 'Stable' ? 'bg-green-600 text-white' :
                          status === 'Critical' ? 'bg-red-600 text-white' :
                          status === 'Analyzing' ? 'bg-indigo-600 text-white' :
                          'bg-zinc-700 text-white'
                        : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-zinc-400">Full Project Manifest & Parameters</label>
              <div className="group relative">
                <svg className="w-3.5 h-3.5 text-zinc-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="absolute left-full ml-2 bottom-0 w-64 p-3 bg-zinc-800 text-[10px] text-zinc-300 rounded shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                   Detail the technical constraints, target metrics, and bottlenecks.
                </div>
              </div>
            </div>
            <div className="relative">
              <textarea 
                rows={6}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all resize-none pr-12"
                placeholder="Detailed technical overview..."
                value={projectMetadata.description}
                onChange={(e) => onUpdateMetadata({ ...projectMetadata, description: e.target.value })}
              />
              <button
                onClick={() => startListening('description')}
                className={`absolute right-3 bottom-3 p-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:text-white transition-all ${isListening === 'description' ? 'text-red-500 animate-pulse border-red-500' : 'text-zinc-500'}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-zinc-800/50">
            <div className="flex gap-4">
              <span className="flex items-center gap-2 text-xs text-zinc-500">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Deep Intel reasoning engine active
              </span>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => startListening('command')}
                disabled={loading || !!isListening}
                title="Voice Command (e.g., 'Execute Synthesis')"
                className={`flex items-center justify-center w-12 h-12 rounded-lg transition-all border ${
                  isListening === 'command'
                    ? 'bg-red-600/20 border-red-500 text-red-500 animate-pulse' 
                    : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-white hover:bg-zinc-700'
                }`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </button>

              <button 
                disabled={loading}
                onClick={handleDeepAnalysis}
                className="flex items-center gap-2 px-8 py-3 rounded-lg font-semibold transition-all bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Execute Synthesis
              </button>
            </div>
          </div>
        </div>
      </div>

      {isListening && (
        <div className="flex justify-center">
          <p className="text-xs font-mono text-indigo-400 animate-pulse uppercase tracking-widest">
             {isListening === 'command' ? 'Awaiting Natural Language Command...' : `Recording ${isListening}...`}
          </p>
        </div>
      )}

      <div className="bg-[#111115] border border-zinc-800 rounded-xl p-8">
        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <svg className="w-5 h-5 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Historical Scans
        </h3>

        {history.length > 0 ? (
          <div className="space-y-4">
            {history.map((item) => (
              <div 
                key={item.id} 
                onClick={() => onResults(item.result)}
                className="flex items-center justify-between p-4 bg-zinc-900/30 border border-zinc-800/50 rounded-xl hover:bg-zinc-900/50 hover:border-indigo-500/30 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-1.5 h-1.5 rounded-full ${item.status === 'Stable' ? 'bg-green-500' : 'bg-indigo-500'}`} />
                  <div>
                    <p className="text-sm font-medium text-white group-hover:text-indigo-300 transition-colors">{item.projectName}</p>
                    <p className="text-[10px] text-zinc-600">{item.timestamp}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-zinc-600 px-2 py-0.5 border border-zinc-800 rounded">{item.id.slice(0, 8)}</span>
                  <svg className="w-4 h-4 text-zinc-700 group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 border border-dashed border-zinc-800 rounded-xl">
            <p className="text-zinc-600 text-sm">Scan log empty.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceModule;
