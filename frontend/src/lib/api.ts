import type { AlertRecord, AcademicRecord, CurrentUserResponse, FacultyStudentSummary, RiskAssessment, TokenResponse } from '../types'

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'
const AUTH_TOKEN_KEY = 'student-alerting-token'

export const getApiBaseUrl = () => {
  const configured = import.meta.env.VITE_API_BASE_URL
  return (configured ?? DEFAULT_API_BASE_URL).replace(/\/$/, '')
}

export const getStoredToken = () => localStorage.getItem(AUTH_TOKEN_KEY)

export const setStoredToken = (token: string | null) => {
  if (!token) {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    return
  }

  localStorage.setItem(AUTH_TOKEN_KEY, token)
}

export const getAuthHeaders = (token?: string) => {
  const activeToken = token ?? getStoredToken()
  return {
    Accept: 'application/json',
    ...(activeToken ? { Authorization: `Bearer ${activeToken}` } : {}),
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers: {
      ...getAuthHeaders(token),
      ...(options.headers ?? {}),
      ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    },
  })

  if (!response.ok) {
    let detail: string | undefined
    try {
      const payload = (await response.json()) as { detail?: string; message?: string }
      detail = payload?.detail ?? payload?.message
    } catch {
      detail = undefined
    }

    throw new Error(detail ?? `Request failed with status ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string, token?: string) => request<T>(path, { method: 'GET' }, token),
  post: <T>(path: string, body: unknown, token?: string) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }, token),
  patch: <T>(path: string, body: unknown, token?: string) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }, token),
}

export type AuthRequest = {
  email: string
  password: string
}

export const authApi = {
  login: (payload: AuthRequest) => api.post<TokenResponse>('/api/auth/login', payload),
  register: (payload: AuthRequest) => api.post<CurrentUserResponse>('/api/auth/register', payload),
  me: (token?: string) => api.get<CurrentUserResponse>('/api/auth/me', token),
}

export const studentApi = {
  profile: (token?: string) => api.get<CurrentUserResponse['student']>('/api/student/me', token),
  academicRecords: (token?: string) => api.get<AcademicRecord[]>('/api/student/me/academic-records', token),
  risk: (token?: string) => api.get<RiskAssessment>('/api/student/me/risk', token),
}

export const facultyApi = {
  profile: (token?: string) => api.get<CurrentUserResponse['faculty']>('/api/faculty/me', token),
  students: (token?: string) => api.get<FacultyStudentSummary[]>('/api/faculty/students', token),
  studentsAtRisk: (token?: string) => api.get<FacultyStudentSummary[]>('/api/faculty/students-at-risk', token),
  studentDetail: (studentId: number, token?: string) =>
    api.get<FacultyStudentSummary & { academic_records?: AcademicRecord[]; risk_assessment?: RiskAssessment }>('/api/faculty/students/' + studentId, token),
  alerts: (token?: string) => api.get<AlertRecord[]>('/api/alerts', token),
  updateAlertStatus: (alertId: number, status: AlertRecord['status'], token?: string) =>
    api.patch<AlertRecord>('/api/alerts/' + alertId + '/status', { status }, token),
}
