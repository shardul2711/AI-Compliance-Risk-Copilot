const API_BASE_URL = 'http://localhost:8000/api';

class ApiService {
  private getHeaders(isMultipart = false): HeadersInit {
    const headers: Record<string, string> = {};
    
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    
    return headers;
  }

  // Auth API
  async register(name: string, email: string, password: string, role = 'Analyst'): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ name, email, password, role }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Registration failed');
    }
    return response.json();
  }

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    // OAuth2PasswordRequestForm expects urlencoded form data
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await response.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', data.access_token);
    }
    return data;
  }

  async getCurrentUser(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
      }
      throw new Error('Unauthorized');
    }
    return response.json();
  }

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  // Documents API
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return response.json();
  }

  async getDocuments(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to retrieve documents');
    }
    return response.json();
  }

  async getDocumentDetails(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to retrieve document details');
    }
    return response.json();
  }

  async deleteDocument(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to delete document');
    }
    return response.json();
  }

  async analyzeDocument(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}/analyze`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to start analysis');
    }
    return response.json();
  }

  async chatDocument(id: number, message: string): Promise<{ answer: string; retrieved_chunks: string[] }> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      throw new Error('Failed to send chat message');
    }
    return response.json();
  }

  async getDocumentRisk(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}/risk`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to retrieve risk score');
    }
    return response.json();
  }

  async getDocumentReport(id: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}/report`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to retrieve report');
    }
    return response.json();
  }

  // Audits API
  async getAuditLogs(documentId?: number): Promise<any[]> {
    const url = documentId 
      ? `${API_BASE_URL}/audit?document_id=${documentId}`
      : `${API_BASE_URL}/audit`;
      
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to retrieve audit logs');
    }
    return response.json();
  }
}

export const apiService = new ApiService();
