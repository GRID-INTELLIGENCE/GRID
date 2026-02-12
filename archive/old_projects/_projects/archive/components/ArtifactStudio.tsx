
import React, { useState } from 'react';
import { AnalysisResult, Artifact } from '../types';

interface ArtifactStudioProps {
  analysis: AnalysisResult | null;
}

const ArtifactStudio: React.FC<ArtifactStudioProps> = ({ analysis }) => {
  const [selectedTab, setSelectedTab] = useState<'summary' | 'intel' | 'excel' | 'guidelines'>('summary');

  const exportAsJSON = () => {
    if (!analysis) return;
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stratagem_artifact_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportAsCSV = () => {
    if (!analysis) return;
    let csv = "Category,Content\n";
    csv += `"Executive Summary","${analysis.executiveSummary.replace(/"/g, '""')}"\n`;
    analysis.bottlenecks.forEach((b, i) => {
      csv += `"Bottleneck ${i+1}","${b.replace(/"/g, '""')}"\n`;
    });
    analysis.architecturalSolutions.forEach((s, i) => {
      csv += `"Solution ${i+1}","${s.replace(/"/g, '""')}"\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stratagem_artifact_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!analysis) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-zinc-500 space-y-4">
        <svg className="w-16 h-16 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p className="text-lg">No intelligence data detected.</p>
        <p className="text-sm">Run a 'Deep Intel' scan to populate the Artifact Foundry.</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Studio Artifact Foundry</h2>
          <p className="text-zinc-400">Manufacturing-ready structural integrity reports.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={exportAsCSV}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors border border-zinc-700"
          >
            Export .CSV
          </button>
          <button 
            onClick={exportAsJSON}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors border border-zinc-700"
          >
            Export .JSON
          </button>
        </div>
      </div>

      <div className="bg-[#111115] border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="flex border-b border-zinc-800 overflow-x-auto whitespace-nowrap scrollbar-hide">
          {(['summary', 'intel', 'excel', 'guidelines'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              className={`px-8 py-4 text-sm font-medium transition-all relative ${
                selectedTab === tab ? 'text-white bg-zinc-900/50' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {tab === 'intel' ? 'Market Intel' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              {selectedTab === tab && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500" />}
            </button>
          ))}
        </div>

        <div className="p-8">
          {selectedTab === 'summary' && (
            <div className="space-y-8 animate-in fade-in duration-500">
              <section>
                <h3 className="text-xl font-semibold mb-4 text-indigo-400">Executive Brief</h3>
                <div className="prose prose-invert max-w-none text-zinc-300 leading-relaxed">
                  {analysis.executiveSummary}
                </div>
              </section>

              <div className="grid md:grid-cols-2 gap-8">
                <section className="bg-zinc-900/50 p-6 rounded-xl border border-zinc-800">
                  <h4 className="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-4">Critical Bottlenecks</h4>
                  <ul className="space-y-3">
                    {analysis.bottlenecks.map((b, i) => (
                      <li key={i} className="flex gap-3 text-sm text-zinc-300">
                        <span className="text-red-500 mt-1">●</span> {b}
                      </li>
                    ))}
                  </ul>
                </section>
                <section className="bg-zinc-900/50 p-6 rounded-xl border border-zinc-800">
                  <h4 className="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-4">Architectural Solutions</h4>
                  <ul className="space-y-3">
                    {analysis.architecturalSolutions.map((s, i) => (
                      <li key={i} className="flex gap-3 text-sm text-zinc-300">
                        <span className="text-green-500 mt-1">◆</span> {s}
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
            </div>
          )}

          {selectedTab === 'intel' && (
            <div className="space-y-8 animate-in fade-in duration-500">
              <section>
                <h3 className="text-xl font-semibold mb-4 text-indigo-400">Real-time Market Intelligence</h3>
                <div className="prose prose-invert max-w-none text-zinc-300 leading-relaxed whitespace-pre-wrap bg-zinc-900/30 p-6 rounded-xl border border-zinc-800/50">
                  {analysis.marketIntelligenceText || "Generating market intelligence..."}
                </div>
              </section>

              {analysis.groundingSources.length > 0 && (
                <section>
                  <h4 className="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-4">Verification Sources</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {analysis.groundingSources.map((source, i) => (
                      <a 
                        key={i} 
                        href={source.web.uri} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-4 bg-zinc-950 border border-zinc-800 rounded-lg hover:border-indigo-500/50 transition-all group"
                      >
                        <p className="text-xs text-indigo-400 mb-1 group-hover:underline truncate">{source.web.title}</p>
                        <p className="text-[10px] text-zinc-600 truncate">{source.web.uri}</p>
                      </a>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}

          {selectedTab === 'excel' && (
            <div className="animate-in fade-in duration-500 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-zinc-500 font-mono uppercase text-[10px] border-b border-zinc-800">
                  <tr>
                    <th className="py-3 px-4">Component ID</th>
                    <th className="py-3 px-4">Classification</th>
                    <th className="py-3 px-4">Risk Level</th>
                    <th className="py-3 px-4">Solution Vector</th>
                    <th className="py-3 px-4">Stability Index</th>
                  </tr>
                </thead>
                <tbody className="text-zinc-300 font-mono">
                  {analysis.bottlenecks.map((b, i) => (
                    <tr key={i} className="border-b border-zinc-900/50 hover:bg-zinc-900/20 transition-colors">
                      <td className="py-4 px-4 text-indigo-400">#STR-{100 + i}</td>
                      <td className="py-4 px-4">Bottleneck</td>
                      <td className="py-4 px-4">
                        <span className="px-2 py-0.5 bg-red-950 text-red-400 border border-red-900 rounded text-[10px]">CRITICAL</span>
                      </td>
                      <td className="py-4 px-4 truncate max-w-xs">{analysis.architecturalSolutions[i] || 'Analysis Pending'}</td>
                      <td className="py-4 px-4">34%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-8 flex justify-end">
                <button 
                  onClick={exportAsCSV}
                  className="flex items-center gap-2 px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded-lg text-xs font-bold transition-all"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" /><path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" /></svg>
                  Export Data to CSV
                </button>
              </div>
            </div>
          )}

          {selectedTab === 'guidelines' && (
            <div className="space-y-6 animate-in fade-in duration-500">
              <h3 className="text-lg font-semibold text-zinc-100 mb-6 flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-indigo-500 flex items-center justify-center text-[10px]">S</div>
                Step-by-Step Manufacturing Guidelines
              </h3>
              <div className="space-y-12 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-zinc-800">
                {analysis.architecturalSolutions.map((sol, i) => (
                  <div key={i} className="relative pl-10">
                    <div className="absolute left-0 top-0 w-6 h-6 bg-zinc-900 border border-zinc-700 rounded-full flex items-center justify-center text-xs font-bold text-indigo-500 z-10">
                      {i + 1}
                    </div>
                    <div className="p-6 bg-zinc-900/30 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors">
                      <h4 className="font-medium text-white mb-2">{sol}</h4>
                      <p className="text-sm text-zinc-500">
                        Implement the defined architectural solution by mapping secondary dependencies.
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArtifactStudio;
