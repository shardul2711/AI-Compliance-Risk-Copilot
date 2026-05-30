'use client';

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '../../services/api';
import { UploadCloud, File, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successDoc, setSuccessDoc] = useState<any | null>(null);
  
  const router = useRouter();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    setError(null);
    setSuccessDoc(null);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      const selectedFile = droppedFiles[0];
      if (selectedFile.type === 'application/pdf' || selectedFile.name.endsWith('.pdf')) {
        setFile(selectedFile);
      } else {
        setError('Unsupported format. Please upload a PDF document.');
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccessDoc(null);
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.pdf')) {
        setFile(selectedFile);
      } else {
        setError('Unsupported format. Please upload a PDF document.');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const doc = await apiService.uploadDocument(file);
      setSuccessDoc(doc);
      setFile(null);
    } catch (err: any) {
      setError(err.message || 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6 font-sans">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">Document Ingestion Workspace</h1>
        <p className="text-xs text-slate-400 mt-1">Upload contracts, NDAs, policies, or regulatory agreements in PDF format to trigger GRC compliance mappings.</p>
      </div>

      {/* Upload Drag and Drop Panel */}
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 min-h-[280px]
          ${dragging ? 'border-indigo-500 bg-indigo-500/5' : 'border-slate-800 bg-slate-900/40 hover:bg-slate-900/60'}
        `}
      >
        <input 
          type="file" 
          id="file-input"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden" 
        />
        <label htmlFor="file-input" className="cursor-pointer flex flex-col items-center">
          <div className="p-4 bg-slate-950/80 rounded-full border border-slate-800 text-slate-400 mb-4 shadow-inner">
            <UploadCloud size={32} className={uploading ? "animate-bounce" : ""} />
          </div>
          <span className="text-sm font-bold text-slate-200 block">Drag & drop your PDF file here</span>
          <span className="text-xs text-slate-500 mt-1 block">or click to browse local files</span>
          <span className="text-[10px] text-indigo-400/70 border border-indigo-500/10 px-2 py-0.5 rounded bg-indigo-500/5 mt-4 inline-block font-semibold">Supports PDFs up to 50MB</span>
        </label>
      </div>

      {/* Selected File Card */}
      {file && (
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg">
              <File size={20} />
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">{file.name}</p>
              <p className="text-[10px] text-slate-400 font-medium">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-850 text-white rounded-lg text-xs font-semibold tracking-wide active:scale-[0.98] transition-all duration-200"
          >
            {uploading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Uploading...
              </>
            ) : (
              <>
                Process File
                <ArrowRight size={14} />
              </>
            )}
          </button>
        </div>
      )}

      {/* Success Notification */}
      {successDoc && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-3 shadow-lg">
          <CheckCircle2 className="text-emerald-400 shrink-0 mt-0.5" size={18} />
          <div className="flex-1 space-y-1">
            <h4 className="text-xs font-bold text-slate-100">Document Uploaded Successfully</h4>
            <p className="text-[10px] text-slate-400 leading-normal">
              `{successDoc.filename}` has been loaded. Ready to run agent audits and ML scoring.
            </p>
            <div className="pt-2 flex gap-4">
              <button 
                onClick={() => router.push('/documents')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-bold transition-colors flex items-center gap-1"
              >
                Go to Document Inventory
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3 shadow-lg">
          <AlertCircle className="text-rose-400 shrink-0 mt-0.5" size={18} />
          <div>
            <h4 className="text-xs font-bold text-slate-100 font-sans">Ingestion Failed</h4>
            <p className="text-[10px] text-rose-400 mt-1 leading-normal font-sans">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
