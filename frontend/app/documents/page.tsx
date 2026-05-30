'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../../services/api';
import { 
  FileText, 
  Play, 
  Trash2, 
  MessageSquare, 
  Eye, 
  ShieldAlert, 
  Calendar,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);

  // Fetch documents list with React Query
  const { data: documents = [], isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiService.getDocuments(),
    refetchInterval: 5000, // poll every 5s during processing
  });

  // Mutation: Trigger LangGraph Analysis
  const analyzeMutation = useMutation({
    mutationFn: (id: number) => apiService.analyzeDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to start analysis.');
    }
  });

  // Mutation: Delete Document
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to delete document.');
    }
  });

  const handleAnalyze = (id: number) => {
    setActionError(null);
    analyzeMutation.mutate(id);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this document and all its AI analysis? This action is permanent.')) {
      setActionError(null);
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">Document Inventory</h1>
        <p className="text-xs text-slate-400 mt-1">Manage uploaded policy agreements and run multi-agent audits to generate compliance indexes.</p>
      </div>

      {/* Action Errors */}
      {actionError && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3 shadow-lg">
          <AlertCircle className="text-rose-400 shrink-0 mt-0.5" size={18} />
          <div>
            <h4 className="text-xs font-bold text-slate-100">Operation Error</h4>
            <p className="text-[10px] text-rose-400 mt-1 leading-normal">{actionError}</p>
          </div>
        </div>
      )}

      {/* Document Grid/Table */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-slate-400">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-xs font-medium">Retrieving agreement repository...</p>
          </div>
        ) : error ? (
          <div className="p-16 text-center text-rose-400 text-xs font-semibold">
            Failed to retrieve documents. Make sure backend FastAPI server is running.
          </div>
        ) : documents.length === 0 ? (
          <div className="p-16 text-center text-slate-400 space-y-4">
            <FileText className="mx-auto text-slate-600" size={48} />
            <div className="max-w-xs mx-auto">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">No Agreements Found</h3>
              <p className="text-xs text-slate-500 mt-1">Get started by importing a contract or NDAs inside the ingestion portal.</p>
            </div>
            <Link 
              href="/upload"
              className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold tracking-wide"
            >
              Upload PDF
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/40 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">Document Type</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Risk Rating</th>
                  <th className="px-6 py-4">Upload Timestamp</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 text-xs text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-850/30 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-200 max-w-[200px] truncate">{doc.filename}</td>
                    <td className="px-6 py-4">
                      {doc.document_type ? (
                        <span className="px-2 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-medium">
                          {doc.document_type}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Pending classification</span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-semibold">
                      {doc.status === 'Uploaded' && (
                        <span className="text-slate-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                          Pending Analysis
                        </span>
                      )}
                      {doc.status === 'Processing' && (
                        <span className="text-amber-400 flex items-center gap-1.5 font-bold">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
                          Running Agents...
                        </span>
                      )}
                      {doc.status === 'Analyzed' && (
                        <span className="text-emerald-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Audit Complete
                        </span>
                      )}
                      {doc.status === 'Failed' && (
                        <span className="text-rose-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                          Failed
                        </span>
                      )}
                      {doc.status === 'Processed' && (
                        <span className="text-blue-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                          Ready to Analyze
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-bold">
                      {doc.risk_score !== null && doc.risk_score !== undefined ? (
                        <span className={`
                          ${doc.risk_level === 'Low' && 'text-emerald-400'}
                          ${doc.risk_level === 'Medium' && 'text-amber-400'}
                          ${doc.risk_level === 'High' && 'text-rose-400'}
                          ${doc.risk_level === 'Critical' && 'text-rose-600 font-extrabold'}
                        `}>
                          {doc.risk_score}/100 ({doc.risk_level})
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">No score</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Calendar size={13} />
                        {new Date(doc.uploaded_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end items-center gap-3">
                        {/* Analyze Trigger */}
                        {(doc.status === 'Uploaded' || doc.status === 'Failed' || doc.status === 'Processed') && (
                          <button
                            onClick={() => handleAnalyze(doc.id)}
                            disabled={analyzeMutation.isPending}
                            className="flex items-center gap-1 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[10px] tracking-wide active:scale-[0.98] transition-all"
                          >
                            <Play size={10} fill="white" />
                            Trigger Audit
                          </button>
                        )}

                        {/* Processing Status Block */}
                        {doc.status === 'Processing' && (
                          <button
                            disabled
                            className="px-3 py-1.5 rounded bg-slate-800 text-slate-500 border border-slate-750 font-semibold text-[10px] tracking-wide"
                          >
                            Analyzing...
                          </button>
                        )}

                        {/* View Results Link */}
                        {doc.status === 'Analyzed' && (
                          <>
                            <Link
                              href={`/analysis/${doc.id}`}
                              className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-750 font-semibold text-[10px] tracking-wide"
                            >
                              <Eye size={11} />
                              Inspection
                            </Link>
                            <Link
                              href={`/chat/${doc.id}`}
                              className="flex items-center gap-1 px-2.5 py-1.5 rounded bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 font-semibold text-[10px] tracking-wide"
                            >
                              <MessageSquare size={11} />
                              Chat RAG
                            </Link>
                          </>
                        )}

                        {/* Delete Button */}
                        <button
                          onClick={() => handleDelete(doc.id)}
                          disabled={deleteMutation.isPending}
                          className="p-1.5 rounded border border-rose-500/20 text-rose-400 bg-rose-500/5 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
                          title="Delete agreement"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
