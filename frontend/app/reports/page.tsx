'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../services/api';
import { FileCheck, Sparkles, Calendar, ChevronRight } from 'lucide-react';

// Simple Markdown Renderer
function MarkdownRenderer({ content }: { content: string }) {
  if (!content) return <p className="text-slate-400">Loading report content...</p>;

  const lines = content.split('\n');
  return (
    <div className="space-y-4 text-xs leading-relaxed text-slate-350">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        
        if (trimmed.startsWith('# ')) {
          return <h2 key={idx} className="text-base font-bold text-slate-100 mt-6 mb-2 border-b border-slate-800 pb-2">{trimmed.slice(2)}</h2>;
        }
        if (trimmed.startsWith('## ')) {
          return <h3 key={idx} className="text-sm font-bold text-indigo-400 mt-5 mb-2">{trimmed.slice(3)}</h3>;
        }
        if (trimmed.startsWith('### ')) {
          return <h4 key={idx} className="text-xs font-bold text-slate-200 mt-4 mb-1">{trimmed.slice(4)}</h4>;
        }
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const text = trimmed.slice(2);
          return (
            <ul key={idx} className="list-disc pl-5 space-y-1">
              <li className="text-slate-350">{renderFormattedText(text)}</li>
            </ul>
          );
        }
        if (trimmed === '---' || trimmed === '***') {
          return <hr key={idx} className="my-6 border-slate-800" />;
        }
        if (trimmed) {
          return <p key={idx} className="mb-3">{renderFormattedText(trimmed)}</p>;
        }
        return <div key={idx} className="h-2" />;
      })}
    </div>
  );
}

function renderFormattedText(text: string) {
  const regex = /\*\*(.*?)\*\*/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    parts.push(<strong key={match.index} className="font-bold text-slate-200">{match[1]}</strong>);
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

export default function ReportsPage() {
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiService.getDocuments(),
  });

  const analyzedDocs = documents.filter(d => d.status === 'Analyzed');
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  // Fetch report for selected document
  const { data: report, isLoading: isLoadingReport } = useQuery({
    queryKey: ['document-report', selectedDocId],
    queryFn: () => apiService.getDocumentReport(selectedDocId!),
    enabled: selectedDocId !== null,
  });

  const activeDoc = analyzedDocs.find(d => d.id === selectedDocId);

  return (
    <div className="flex flex-col lg:flex-row gap-8 h-[calc(100vh-140px)] font-sans">
      
      {/* Left Pane: Documents Selector */}
      <div className="w-full lg:w-80 bg-slate-900 border border-slate-800/80 rounded-xl p-6 flex flex-col gap-4 shadow-lg shrink-0 overflow-y-auto">
        <div>
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Audit Summaries</h2>
          <p className="text-[10px] text-slate-400 mt-1">Select an audited contract to view its executive compliance brief.</p>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500 text-xs">Loading summaries...</div>
        ) : analyzedDocs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">No reports compiled yet. Please run doc analysis first.</div>
        ) : (
          <div className="space-y-2.5">
            {analyzedDocs.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedDocId(doc.id)}
                className={`
                  w-full flex items-center justify-between p-3.5 rounded-lg border text-left transition-all duration-200
                  ${selectedDocId === doc.id 
                    ? 'bg-indigo-600/90 border-indigo-600 text-white shadow-lg shadow-indigo-600/10' 
                    : 'bg-slate-950/40 border-slate-850 text-slate-350 hover:border-slate-800 hover:text-slate-200'
                  }
                `}
              >
                <div className="overflow-hidden space-y-1">
                  <p className="text-xs font-bold truncate pr-2">{doc.filename}</p>
                  <div className="flex items-center gap-1.5 text-[9px] text-slate-450 font-semibold uppercase">
                    <span>{doc.document_type}</span>
                    <span>•</span>
                    <span>Score: {doc.risk_score}</span>
                  </div>
                </div>
                <ChevronRight size={14} className="shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right Pane: Report Viewer */}
      <div className="flex-1 bg-slate-900 border border-slate-800/80 rounded-xl p-8 shadow-lg overflow-y-auto">
        {selectedDocId === null ? (
          <div className="h-full flex flex-col justify-center items-center text-slate-500 space-y-3">
            <FileCheck size={40} className="text-slate-700" />
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-600">Select report to view</p>
          </div>
        ) : isLoadingReport ? (
          <div className="h-full flex flex-col justify-center items-center text-slate-500">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-400">Loading audit markdown...</p>
          </div>
        ) : report ? (
          <div className="space-y-6">
            {/* Header info */}
            <div className="flex justify-between items-start border-b border-slate-800/80 pb-5">
              <div className="space-y-1">
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">{activeDoc?.filename}</h2>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-medium">
                  <Calendar size={12} />
                  <span>Audit date: {activeDoc ? new Date(activeDoc.uploaded_at).toLocaleDateString() : ''}</span>
                </div>
              </div>
              <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border
                ${activeDoc?.risk_level === 'Low' && 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'}
                ${activeDoc?.risk_level === 'Medium' && 'text-amber-400 bg-amber-500/10 border-amber-500/20'}
                ${activeDoc?.risk_level === 'High' && 'text-rose-400 bg-rose-500/10 border-rose-500/20'}
                ${activeDoc?.risk_level === 'Critical' && 'text-rose-600 bg-rose-950/20 border-rose-900/30'}
              `}>
                {activeDoc?.risk_level} Risk ({activeDoc?.risk_score}/100)
              </span>
            </div>
            {/* Report Content */}
            <MarkdownRenderer content={report.summary} />
          </div>
        ) : (
          <div className="p-4 text-center text-rose-400 text-xs">Could not load report contents.</div>
        )}
      </div>
    </div>
  );
}
