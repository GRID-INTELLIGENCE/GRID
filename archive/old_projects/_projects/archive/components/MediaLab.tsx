
import React, { useState } from 'react';
import { gemini } from '../services/geminiService';
import { ImageConfig } from '../types';

const MediaLab: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [config, setConfig] = useState<ImageConfig>({
    aspectRatio: "1:1",
    imageSize: "1K"
  });

  const generateImage = async () => {
    if (!prompt) return;
    setLoading(true);
    try {
      const img = await gemini.generateStudioImage(prompt, config);
      setResultImage(img);
    } catch (error) {
      console.error(error);
      alert("Image generation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      <div className="grid md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <svg className="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Vision Core Generation
            </h2>

            <div className="space-y-4">
              <textarea
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:ring-2 focus:ring-indigo-500 outline-none h-32"
                placeholder="Visualize a technical blueprint of a carbon-neutral manufacturing facility..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-zinc-500 uppercase mb-2">Aspect Ratio</label>
                  <select 
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm text-white outline-none"
                    value={config.aspectRatio}
                    onChange={(e: any) => setConfig({ ...config, aspectRatio: e.target.value })}
                  >
                    <option value="1:1">1:1 Square</option>
                    <option value="16:9">16:9 Landscape</option>
                    <option value="9:16">9:16 Portrait</option>
                    <option value="4:3">4:3 Standard</option>
                    <option value="21:9">21:9 Ultrawide</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-zinc-500 uppercase mb-2">Resolution</label>
                  <select 
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm text-white outline-none"
                    value={config.imageSize}
                    onChange={(e: any) => setConfig({ ...config, imageSize: e.target.value })}
                  >
                    <option value="1K">1K Efficiency</option>
                    <option value="2K">2K Professional</option>
                    <option value="4K">4K Ultra HD</option>
                  </select>
                </div>
              </div>

              <button
                disabled={loading}
                onClick={generateImage}
                className={`w-full py-4 rounded-xl font-bold transition-all ${
                  loading ? 'bg-zinc-800 text-zinc-500' : 'bg-white text-black hover:bg-zinc-200'
                }`}
              >
                {loading ? 'Synthesizing...' : 'Generate Blueprint'}
              </button>
            </div>
          </div>
          
          <div className="bg-zinc-900/30 border border-zinc-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-4">Vision Intelligence</h3>
            <p className="text-xs text-zinc-500 mb-4">Analyze site photos or video walkthroughs with Gemini 3 Pro.</p>
            <div className="flex gap-4">
               <button className="flex-1 py-3 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-bold transition-all border border-zinc-700">
                Upload Image
              </button>
              <button className="flex-1 py-3 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-bold transition-all border border-zinc-700">
                Process Video
              </button>
            </div>
          </div>
        </div>

        <div className="bg-zinc-950 border border-zinc-800 rounded-2xl flex items-center justify-center overflow-hidden min-h-[400px]">
          {resultImage ? (
            <img src={resultImage} alt="Generated result" className="w-full h-full object-contain" />
          ) : (
            <div className="text-center p-12">
              <div className="w-20 h-20 bg-zinc-900 rounded-3xl mx-auto flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-zinc-400 font-medium mb-2">Visualizer Output</h3>
              <p className="text-zinc-600 text-sm">Output will appear here after generation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MediaLab;
