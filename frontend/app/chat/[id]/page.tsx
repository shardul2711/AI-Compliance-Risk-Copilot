'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../../services/api';
import { 
  Send, 
  Bot, 
  User as UserIcon, 
  ArrowLeft, 
  HelpCircle,
  FileText,
  AlertCircle,
  FolderOpen
} from 'lucide-react';
import Link from 'next/link';
import { ChatMessage } from '../../../types';

export default function DocumentChatPage() {
  const { id } = useParams();
  const docId = Number(id);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch document details
  const { data: doc, isLoading } = useQuery({
    queryKey: ['document-details', docId],
    queryFn: () => apiService.getDocumentDetails(docId),
  });

  // Welcome message
  useEffect(() => {
    if (doc) {
      setMessages([
        {
          sender: 'system',
          text: `Hello! I am your AI Compliance Risk Copilot. I have mapped and indexed "${doc.filename}" into the local Qdrant vector store.\n\nYou can ask me specific questions about legal clauses, financial penalties, data security measures, or compliance alignment (GDPR, HIPAA, SOC2). Try clicking one of the preset prompts on the left to start!`
        }
      ]);
    }
  }, [doc]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const presetQueries = [
    "What penalties are mentioned?",
    "What are the termination clauses?",
    "What compliance risks exist?",
    "What is the governing law of this agreement?",
    "Is there a data privacy clause addressing GDPR?"
  ];

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    // User Message
    const userMsg: ChatMessage = { sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);
    setError(null);

    try {
      const res = await apiService.chatDocument(docId, text);
      const botMsg: ChatMessage = {
        sender: 'system',
        text: res.answer,
        retrieved_chunks: res.retrieved_chunks
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err: any) {
      setError('Failed to fetch response. Make sure the local Ollama LLM is running.');
      setMessages(prev => [
        ...prev,
        {
          sender: 'system',
          text: 'Error: Could not retrieve response from Ollama. Ensure "ollama run llama3.1" is running locally.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex flex-col justify-center items-center text-slate-400">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Loading Chat Console...</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8 text-center text-rose-400 text-sm font-bold">
        Document not found.
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 h-[calc(100vh-140px)] font-sans">
      
      {/* Left Panel: Document Info & Presets */}
      <div className="w-full lg:w-80 bg-slate-900 border border-slate-800/80 rounded-xl p-6 flex flex-col justify-between shadow-lg shrink-0">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <Link 
              href="/documents"
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ArrowLeft size={14} />
            </Link>
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">RAG Chat Workspace</h2>
          </div>

          {/* Doc details card */}
          <div className="p-4 bg-slate-950/40 border border-slate-800/60 rounded-lg space-y-3">
            <div className="flex items-start gap-2.5">
              <FileText size={16} className="text-indigo-400 shrink-0 mt-0.5" />
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-slate-200 truncate">{doc.filename}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">{doc.document_type || 'Unclassified'}</p>
              </div>
            </div>
            {doc.risk_assessment && (
              <div className="pt-2.5 border-t border-slate-800/50 flex justify-between items-center text-[10px]">
                <span className="text-slate-450 font-medium">Risk Score:</span>
                <span className={`font-bold uppercase
                  ${doc.risk_assessment.risk_level === 'Low' && 'text-emerald-400'}
                  ${doc.risk_assessment.risk_level === 'Medium' && 'text-amber-400'}
                  ${doc.risk_assessment.risk_level === 'High' && 'text-rose-400'}
                  ${doc.risk_assessment.risk_level === 'Critical' && 'text-rose-600'}
                `}>
                  {doc.risk_assessment.risk_score} ({doc.risk_assessment.risk_level})
                </span>
              </div>
            )}
          </div>

          {/* Presets List */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle size={12} className="text-indigo-400" />
              Quick Compliance Queries
            </h3>
            <div className="space-y-2">
              {presetQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handleSendMessage(query)}
                  disabled={loading}
                  className="w-full text-left p-2.5 rounded-lg bg-slate-950/40 border border-slate-850 hover:border-indigo-500/30 text-[10px] font-semibold text-slate-350 hover:text-slate-200 transition-all duration-200"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800/80 text-[10px] text-slate-500 font-medium flex items-center gap-1">
          <FolderOpen size={12} />
          Qdrant indexing enabled locally
        </div>
      </div>

      {/* Right Panel: Chat Dialogue console */}
      <div className="flex-1 bg-slate-900 border border-slate-800/80 rounded-xl flex flex-col justify-between shadow-lg overflow-hidden h-full">
        {/* Messages list */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.map((msg, index) => {
            const isBot = msg.sender === 'system';
            return (
              <div key={index} className={`flex gap-4 ${isBot ? 'items-start' : 'items-start flex-row-reverse'}`}>
                <div className={`p-2.5 rounded-lg shrink-0
                  ${isBot 
                    ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400' 
                    : 'bg-slate-800 border border-slate-750 text-slate-300'
                  }
                `}>
                  {isBot ? <Bot size={16} /> : <UserIcon size={16} />}
                </div>
                
                <div className="space-y-3 max-w-[80%]">
                  <div className={`p-4 rounded-xl text-xs leading-relaxed font-medium whitespace-pre-line
                    ${isBot 
                      ? 'bg-slate-950/40 border border-slate-850 text-slate-300' 
                      : 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                    }
                  `}>
                    {msg.text}
                  </div>

                  {/* Evidence Drawer for RAG sources */}
                  {isBot && msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                    <details className="group border border-slate-850 rounded-lg overflow-hidden bg-slate-950/20">
                      <summary className="px-4 py-2 text-[10px] font-bold text-slate-450 uppercase tracking-wider cursor-pointer list-none flex items-center justify-between hover:bg-slate-900/30">
                        <span>Show Qdrant Search Citations</span>
                        <ChevronDownIcon />
                      </summary>
                      <div className="p-4 border-t border-slate-850 space-y-3">
                        {msg.retrieved_chunks.map((chunk, idx) => (
                          <div key={idx} className="p-2.5 bg-slate-950 border border-slate-900 rounded font-mono text-[9px] text-slate-500 leading-normal">
                            "{chunk}"
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            );
          })}
          {loading && (
            <div className="flex gap-4 items-start">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0">
                <Bot size={16} />
              </div>
              <div className="py-3 px-4 bg-slate-950/40 border border-slate-850 rounded-xl flex items-center gap-2 text-slate-400 text-xs font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping"></span>
                Searching vectors & synthesizing answer...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* User Input form */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30 flex flex-col gap-3">
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(inputValue);
            }}
            className="flex gap-3"
          >
            <input
              type="text"
              placeholder="Ask a compliance question (e.g. What is the governing law?)"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading}
              className="flex-1 px-4 py-3 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 rounded-lg text-xs text-slate-250 focus:outline-none transition-all duration-200"
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="p-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-850 text-white rounded-lg active:scale-[0.98] transition-all duration-200"
            >
              <Send size={16} />
            </button>
          </form>
          {error && (
            <div className="text-[10px] text-rose-400 font-semibold flex items-center gap-1">
              <AlertCircle size={12} />
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ChevronDownIcon() {
  return (
    <svg className="w-3.5 h-3.5 text-slate-500 transform group-open:rotate-180 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}
