export type UserRole = 'STUDENT' | 'FACULTY' | 'ADMIN'

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface StudentProfile {
  id: number
  student_identifier: string
  first_name: string
  last_name: string
  current_semester: number
  program: string
}

export interface FacultyProfile {
  id: number
  employee_identifier: string
  first_name: string
  last_name: string
  department: string
}

export interface CurrentUserResponse {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
  student?: StudentProfile | null
  faculty?: FacultyProfile | null
}

export interface RiskAssessment {
  student_id?: number
  record_id?: number
  risk_level?: string
  risk_status?: string
  risk_score?: number
  decision_threshold?: number
  prediction_date?: string
  message?: string
  [key: string]: unknown
}

export interface AcademicRecord {
  id: number
  student_id?: number
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

export interface FacultyStudentSummary {
  id: number
  student_identifier?: string
  first_name?: string
  last_name?: string
  program?: string
  latest_record_date?: string
  risk_level?: string
  risk_status?: string
  risk_score?: number
  [key: string]: unknown
}

export interface AlertRecord {
  id: number
  student_id: number
  prediction_id?: number
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE'
  severity: string
  created_at: string
  updated_at: string
}
