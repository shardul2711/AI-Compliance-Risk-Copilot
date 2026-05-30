export interface User {
  id: number;
  name: string;
  email: string;
  role: 'Admin' | 'Analyst';
  created_at: string;
}

export interface Document {
  id: number;
  user_id: number;
  filename: string;
  document_type: 'Contract' | 'NDA' | 'Policy' | 'Regulation' | 'Vendor Agreement' | null;
  status: 'Uploaded' | 'Processing' | 'Analyzed' | 'Failed' | 'Processed';
  uploaded_at: string;
}

export interface Clause {
  id: number;
  document_id: number;
  clause_type: 'Confidentiality' | 'Data Privacy' | 'Liability' | 'Termination' | 'Security' | 'Payment' | 'Audit Rights';
  clause_text: string;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface ComplianceResult {
  id: number;
  document_id: number;
  framework: 'GDPR' | 'HIPAA' | 'SOC2' | 'ISO27001' | 'PCI-DSS';
  requirement: string;
  status: 'Compliant' | 'Non-Compliant' | 'Partially-Compliant';
  gap_description: string | null;
}

export interface RiskAssessment {
  id: number;
  document_id: number;
  risk_score: number;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  prediction_model: string;
}

export interface Recommendation {
  id: number;
  document_id: number;
  recommendation: string;
}

export interface ExecutiveReport {
  id: number;
  document_id: number;
  summary: string;
}

export interface DocumentDetail extends Document {
  clauses: Clause[];
  compliance_results: ComplianceResult[];
  risk_assessment: RiskAssessment | null;
  recommendations: Recommendation[];
  executive_report: ExecutiveReport | null;
}

export interface AuditLog {
  id: number;
  document_id: number | null;
  agent_name: string;
  action: string;
  input_data: string | null;
  output_data: string | null;
  created_at: string;
}

export interface ChatMessage {
  sender: 'user' | 'system';
  text: string;
  retrieved_chunks?: string[];
}
