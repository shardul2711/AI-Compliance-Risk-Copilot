'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../services/api';
import { History, Eye, EyeOff, Search, Calendar, Cpu } from 'lucide-react';
import { AuditLog } from '../../types';

export default function AuditLogsPage() {
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all audit logs
  const { data: logs = [], isLoading, error } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => apiService.getAuditLogs(),
    refetchInterval: 10000, // refresh every 10s to capture live agent runs!
  });

  const toggleExpandLog = (id: number) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  // Filter logs by search query (matching agent name, action, or payload string)
  const filteredLogs = logs.filter(log => {
    const q = searchQuery.toLowerCase();
    return (
      log.agent_name.toLowerCase().includes(q) ||
      log.action.toLowerCase().includes(q) ||
      (log.input_data && log.input_data.toLowerCase().includes(q)) ||
      (log.output_data && log.output_data.toLowerCase().includes(q))
    );
  });

  const formatJson = (jsonStr: string | null) => {
    if (!jsonStr) return 'None';
    try {
      const parsed = JSON.parse(jsonStr);
      return JSON.stringify(parsed, null, 2);
    } catch (e) {
      return jsonStr;
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 font-sans">AI Decision Audit Trail</h1>
          <p className="text-xs text-slate-400 mt-1">Immutable ledger of LLM inputs, classification weights, ML prediction scores, and SHAP explainer attributes.</p>
        </div>
        
        {/* Search Input bar */}
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
          <input
            type="text"
            placeholder="Search agents or actions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 rounded-lg text-xs text-slate-200 focus:outline-none transition-all duration-200"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900 border border-slate-800/80 rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-slate-400">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-xs font-medium">Fetching decision audit log...</p>
          </div>
        ) : error ? (
          <div className="p-16 text-center text-rose-450 text-xs font-semibold">
            Failed to retrieve audit logs. Make sure backend FastAPI server is running.
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-16 text-center text-slate-500 space-y-3">
            <History className="mx-auto text-slate-700" size={40} />
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-600">No logs found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/40 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <th className="px-6 py-4 w-12"></th>
                  <th className="px-6 py-4">Agent Name</th>
                  <th className="px-6 py-4">Action</th>
                  <th className="px-6 py-4">Document ID</th>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 text-xs text-slate-350">
                {filteredLogs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  return (
                    <React.Fragment key={log.id}>
                      <tr 
                        className={`hover:bg-slate-850/20 transition-colors cursor-pointer ${isExpanded ? 'bg-slate-850/10' : ''}`}
                        onClick={() => toggleExpandLog(log.id)}
                      >
                        <td className="px-6 py-4 text-center">
                          <Cpu size={14} className="text-slate-500" />
                        </td>
                        <td className="px-6 py-4 font-semibold text-slate-200">
                          <span className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                            {log.agent_name}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-300">{log.action}</td>
                        <td className="px-6 py-4 text-slate-450 font-bold">Doc #{log.document_id || 'N/A'}</td>
                        <td className="px-6 py-4 text-slate-450 font-medium">
                          <div className="flex items-center gap-1.5">
                            <Calendar size={13} />
                            {new Date(log.created_at).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleExpandLog(log.id);
                            }}
                            className="p-1 rounded bg-slate-800 hover:bg-slate-750 border border-slate-750 text-slate-300 transition-colors"
                            title={isExpanded ? 'Collapse Payload' : 'Expand Payload'}
                          >
                            {isExpanded ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded Section */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={6} className="px-8 py-5 bg-slate-950/50 border-t border-b border-slate-850">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {/* Input Data payload */}
                              <div className="space-y-2">
                                <h5 className="text-[10px] font-bold text-slate-450 uppercase tracking-widest">Agent Input Parameters</h5>
                                <pre className="bg-slate-950 p-4 border border-slate-850 rounded-lg text-[9px] font-mono overflow-auto max-h-56 text-indigo-300 leading-normal scrollbar-thin">
                                  {formatJson(log.input_data)}
                                </pre>
                              </div>

                              {/* Output Data payload */}
                              <div className="space-y-2">
                                <h5 className="text-[10px] font-bold text-slate-450 uppercase tracking-widest">Agent Decision Response</h5>
                                <pre className="bg-slate-950 p-4 border border-slate-850 rounded-lg text-[9px] font-mono overflow-auto max-h-56 text-emerald-400 leading-normal scrollbar-thin">
                                  {formatJson(log.output_data)}
                                </pre>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
