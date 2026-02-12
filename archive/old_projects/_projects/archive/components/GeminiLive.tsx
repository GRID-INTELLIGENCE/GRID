
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';
import { decodeAudioData, decode, encode } from '../services/audioUtils';

const GeminiLive: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState('Standby');
  const [transcript, setTranscript] = useState<string[]>([]);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef(0);
  const sourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const sessionPromiseRef = useRef<Promise<any> | null>(null);

  const startSession = async () => {
    setIsActive(true);
    setStatus('Connecting...');
    
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
    
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    const outputNode = audioContextRef.current.createGain();
    outputNode.connect(audioContextRef.current.destination);

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const inputAudioContext = new AudioContext({ sampleRate: 16000 });

    sessionPromiseRef.current = ai.live.connect({
      model: 'gemini-2.5-flash-native-audio-preview-09-2025',
      callbacks: {
        onopen: () => {
          setStatus('Active');
          const source = inputAudioContext.createMediaStreamSource(stream);
          const scriptProcessor = inputAudioContext.createScriptProcessor(4096, 1, 1);
          scriptProcessor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const l = inputData.length;
            const int16 = new Int16Array(l);
            for (let i = 0; i < l; i++) int16[i] = inputData[i] * 32768;
            
            const pcmBlob = {
              data: encode(new Uint8Array(int16.buffer)),
              mimeType: 'audio/pcm;rate=16000',
            };
            
            sessionPromiseRef.current?.then(session => {
              session.sendRealtimeInput({ media: pcmBlob });
            });
          };
          source.connect(scriptProcessor);
          scriptProcessor.connect(inputAudioContext.destination);
        },
        onmessage: async (message: LiveServerMessage) => {
          const audioBase64 = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
          if (audioBase64 && audioContextRef.current) {
            nextStartTimeRef.current = Math.max(nextStartTimeRef.current, audioContextRef.current.currentTime);
            const buffer = await decodeAudioData(decode(audioBase64), audioContextRef.current, 24000, 1);
            const source = audioContextRef.current.createBufferSource();
            source.buffer = buffer;
            source.connect(outputNode);
            source.start(nextStartTimeRef.current);
            nextStartTimeRef.current += buffer.duration;
            sourcesRef.current.add(source);
            source.onended = () => sourcesRef.current.delete(source);
          }

          if (message.serverContent?.interrupted) {
            sourcesRef.current.forEach(s => s.stop());
            sourcesRef.current.clear();
            nextStartTimeRef.current = 0;
          }
        },
        onerror: () => setStatus('Error'),
        onclose: () => {
          setIsActive(false);
          setStatus('Closed');
        }
      },
      config: {
        responseModalities: [Modality.AUDIO],
        systemInstruction: 'You are the Stratagem Intelligence Voice Assistant. Help users map project states, analyze architecture, and find bottlenecks via conversation.',
        speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } }
      }
    });
  };

  const stopSession = () => {
    sessionPromiseRef.current?.then(s => s.close());
    setIsActive(false);
    setStatus('Standby');
  };

  return (
    <div className="max-w-4xl mx-auto py-12">
      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
        <div className="p-12 flex flex-col items-center justify-center text-center space-y-8">
          <div className="relative">
            <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-1000 ${
              isActive ? 'bg-indigo-600/20 scale-110' : 'bg-zinc-800'
            }`}>
              <div className={`w-24 h-24 rounded-full flex items-center justify-center ${
                isActive ? 'bg-indigo-500 animate-pulse shadow-2xl shadow-indigo-500/50' : 'bg-zinc-700'
              }`}>
                <svg className={`w-12 h-12 ${isActive ? 'text-white' : 'text-zinc-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
            </div>
            {isActive && (
              <div className="absolute -inset-4 rounded-full border border-indigo-500/30 animate-ping duration-[3000ms]" />
            )}
          </div>

          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Live Intelligence Link</h2>
            <p className="text-zinc-400">Conversational access to Gemini 2.5 Native Audio Bridge.</p>
          </div>

          <div className="px-4 py-1.5 bg-zinc-950 rounded-full border border-zinc-800 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500 shadow-sm shadow-green-500' : 'bg-zinc-700'}`} />
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{status}</span>
          </div>

          <button
            onClick={isActive ? stopSession : startSession}
            className={`px-12 py-4 rounded-full font-bold transition-all ${
              isActive 
                ? 'bg-red-600/10 text-red-500 border border-red-500/50 hover:bg-red-600/20' 
                : 'bg-white text-black hover:bg-zinc-200'
            }`}
          >
            {isActive ? 'Disconnect Session' : 'Establish Link'}
          </button>
        </div>

        <div className="bg-zinc-950/50 p-6 border-t border-zinc-800">
           <p className="text-xs text-center text-zinc-600">
             Secure audio bridge established via distributed infrastructure. Your session is transient and analyzed for project intelligence only.
           </p>
        </div>
      </div>
    </div>
  );
};

export default GeminiLive;
