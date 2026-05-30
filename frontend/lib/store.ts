import { create } from 'zustand';
import { User, Document } from '../types';
import { apiService } from '../services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string, role?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<User | null>;
  clearError: () => void;
}

interface DocState {
  documents: Document[];
  selectedDocument: Document | null;
  isLoadingDocs: boolean;
  fetchDocuments: () => Promise<void>;
  setSelectedDocument: (doc: Document | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.login(email, password);
      const user = await apiService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
      return user;
    } catch (err: any) {
      const errMsg = err.message || 'Login failed';
      set({ error: errMsg, isLoading: false });
      throw new Error(errMsg);
    }
  },

  register: async (name, email, password, role) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.register(name, email, password, role);
      set({ isLoading: false });
    } catch (err: any) {
      const errMsg = err.message || 'Registration failed';
      set({ error: errMsg, isLoading: false });
      throw new Error(errMsg);
    }
  },

  logout: () => {
    apiService.logout();
    set({ user: null, isAuthenticated: false, error: null });
  },

  checkAuth: async () => {
    if (typeof window === 'undefined') return null;
    const token = localStorage.getItem('token');
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return null;
    }
    
    set({ isLoading: true, error: null });
    try {
      const user = await apiService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
      return user;
    } catch (err) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return null;
    }
  },
  
  clearError: () => set({ error: null })
}));

export const useDocStore = create<DocState>((set) => ({
  documents: [],
  selectedDocument: null,
  isLoadingDocs: false,

  fetchDocuments: async () => {
    set({ isLoadingDocs: true });
    try {
      const docs = await apiService.getDocuments();
      set({ documents: docs, isLoadingDocs: false });
    } catch (err) {
      set({ isLoadingDocs: false });
    }
  },

  setSelectedDocument: (doc) => set({ selectedDocument: doc }),
}));
