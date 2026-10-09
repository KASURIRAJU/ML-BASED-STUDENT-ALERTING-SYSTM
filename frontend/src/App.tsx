import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import './App.css'
import { authApi, facultyApi, getStoredToken, setStoredToken, studentApi } from './lib/api'
import type { AlertRecord, CurrentUserResponse, UserRole } from './types'

type AuthContextValue = {
  token: string | null
  user: CurrentUserResponse | null
  login: (nextToken: string, nextUser: CurrentUserResponse) => void
  logout: () => void
  refreshUser: () => Promise<CurrentUserResponse | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function getRolePath(role: UserRole | null | undefined) {
  if (role === 'STUDENT') return '/student/dashboard'
  if (role === 'FACULTY') return '/faculty/dashboard'
  return '/login'
}

function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('Auth context not available')
  }

  return context
}

function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [user, setUser] = useState<CurrentUserResponse | null>(null)

  useEffect(() => {
    if (!token) {
      return
    }

    let isMounted = true

    const loadUser = async () => {
      try {
        const currentUser = await authApi.me(token)
        if (isMounted) {
          setUser(currentUser)
        }
      } catch {
        if (isMounted) {
          setStoredToken(null)
          setToken(null)
          setUser(null)
        }
      }
    }

    loadUser()

    return () => {
      isMounted = false
    }
  }, [token])

  const login = useCallback((nextToken: string, nextUser: CurrentUserResponse) => {
    setStoredToken(nextToken)
    setToken(nextToken)
    setUser(nextUser)
  }, [])

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    if (!token) {
      return null
    }

    try {
      const currentUser = await authApi.me(token)
      setUser(currentUser)
      return currentUser
    } catch {
      logout()
      return null
    }
  }, [logout, token])

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, login, logout, refreshUser }),
    [login, logout, refreshUser, token, user],
  )

  if (token && !user) {
    return (
      <div className="page-shell">
        <div className="loading-card">Loading your session…</div>
      </div>
    )
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function RequireAuth({ children, roles }: { children: ReactNode; roles?: UserRole[] }) {
  const { token, user } = useAuth()
  const location = useLocation()

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to={getRolePath(user.role)} replace />
  }

  return <>{children}</>
}

function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()

  if (!user) {
    return <>{children}</>
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">SA</div>
          <div>
            <strong>Student Alerting System</strong>
            <small>{user.role}</small>
          </div>
        </div>
        <nav className="nav-actions">
          {user.role === 'STUDENT' ? (
            <>
              <Link to="/student/dashboard">Dashboard</Link>
              <Link to="/student/academic-records">Academic records</Link>
            </>
          ) : (
            <>
              <Link to="/faculty/dashboard">Dashboard</Link>
              <Link to="/faculty/students">Students</Link>
              <Link to="/faculty/alerts">Alerts</Link>
            </>
          )}
          <button type="button" className="ghost-button" onClick={logout}>
            Log out
          </button>
        </nav>
      </header>
      <main className="content-shell">{children}</main>
    </div>
  )
}

function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const navigate = useNavigate()
  const { login: setAuthSession } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      if (mode === 'register') {
        await authApi.register({ email, password })
      }

      const tokenResponse = await authApi.login({ email, password })
      const user = await authApi.me(tokenResponse.access_token)
      setAuthSession(tokenResponse.access_token, user)
      navigate(getRolePath(user.role))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to complete the request right now.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="page-shell">
      <div className="auth-card">
        <div className="card-header">
          <span className="eyebrow">Access</span>
          <h1>{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={12}
              required
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </label>

          {error ? <div className="error-box">{error}</div> : null}

          <button type="submit" disabled={isSubmitting} className="primary-button">
            {isSubmitting ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Register'}
          </button>
        </form>

        <div className="auth-switcher">
          {mode === 'login' ? (
            <>
              Need an account? <Link to="/register">Register</Link>
            </>
          ) : (
            <>
              Already have an account? <Link to="/login">Log in</Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function StudentDashboardPage() {
  const { token } = useAuth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['student-dashboard', token],
    queryFn: async () => {
      const [profile, records, risk] = await Promise.all([
        studentApi.profile(token ?? undefined),
        studentApi.academicRecords(token ?? undefined),
        studentApi.risk(token ?? undefined),
      ])

      return { profile, records, risk }
    },
    enabled: Boolean(token),
  })

  if (isLoading) return <StatusCard title="Student dashboard" message="Loading student data…" />
  if (error) return <StatusCard title="Student dashboard" type="error" message={error instanceof Error ? error.message : 'Unable to load your data.'} />
  if (!data) return <StatusCard title="Student dashboard" type="empty" message="No student dashboard data is available right now." />

  return (
    <section className="dashboard-grid">
      <div className="panel large-panel">
        <div className="panel-header">
          <h2>Student profile</h2>
        </div>
        <div className="key-value-grid">
          <div><span>Name</span><strong>{data.profile?.first_name ?? 'Unknown'} {data.profile?.last_name ?? ''}</strong></div>
          <div><span>Student ID</span><strong>{data.profile?.student_identifier ?? 'N/A'}</strong></div>
          <div><span>Program</span><strong>{data.profile?.program ?? 'N/A'}</strong></div>
          <div><span>Semester</span><strong>{data.profile?.current_semester ?? 'N/A'}</strong></div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Risk assessment</h2>
        </div>
        {data.risk && typeof data.risk.risk_level === 'string' ? (
          <>
            <div className="risk-badge risk-badge--neutral">{String(data.risk.risk_level)}</div>
            <div className="key-value-grid compact-grid">
              <div><span>Status</span><strong>{String(data.risk.risk_status ?? 'Unknown')}</strong></div>
              <div><span>Score</span><strong>{Number(data.risk.risk_score ?? 0).toFixed(4)}</strong></div>
              <div><span>Threshold</span><strong>{Number(data.risk.decision_threshold ?? 0).toFixed(4)}</strong></div>
            </div>
            <p className="helper-text">
              This risk assessment is decision-support information to guide academic support. It is not a guaranteed prediction of academic failure.
            </p>
          </>
        ) : (
          <StatusCard title="No saved assessment" type="empty" message="No academic record is available for a current risk assessment yet." />
        )}
      </div>

      <div className="panel wide-panel">
        <div className="panel-header split-header">
          <h2>Academic history</h2>
          <Link to="/student/academic-records" className="inline-link">View full list</Link>
        </div>
        {data.records && data.records.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Created</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {data.records.slice(0, 5).map((record) => (
                <tr key={record.id}>
                  <td>{record.id}</td>
                  <td>{record.created_at ? new Date(record.created_at).toLocaleString() : 'N/A'}</td>
                  <td>{record.updated_at ? new Date(record.updated_at).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <StatusCard title="No academic records" type="empty" message="No academic records have been uploaded yet." />
        )}
      </div>
    </section>
  )
}

function StudentAcademicRecordsPage() {
  const { token } = useAuth()
  const { data, isLoading, error } = useQuery({
    queryKey: ['student-academic-records', token],
    queryFn: () => studentApi.academicRecords(token ?? undefined),
    enabled: Boolean(token),
  })

  if (isLoading) return <StatusCard title="Academic records" message="Loading academic records…" />
  if (error) return <StatusCard title="Academic records" type="error" message={error instanceof Error ? error.message : 'Unable to load the records.'} />

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Academic record history</h2>
      </div>
      {data && data.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Created</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {data.map((record) => (
              <tr key={record.id}>
                <td>{record.id}</td>
                <td>{record.created_at ? new Date(record.created_at).toLocaleString() : 'N/A'}</td>
                <td>{record.updated_at ? new Date(record.updated_at).toLocaleString() : 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <StatusCard title="No academic records" type="empty" message="No academic records have been created for this student yet." />
      )}
    </section>
  )
}

function FacultyDashboardPage() {
  const { token } = useAuth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['faculty-dashboard', token],
    queryFn: async () => {
      const [profile, students, atRisk] = await Promise.all([
        facultyApi.profile(token ?? undefined),
        facultyApi.students(token ?? undefined),
        facultyApi.studentsAtRisk(token ?? undefined),
      ])
      return { profile, students, atRisk }
    },
    enabled: Boolean(token),
  })

  if (isLoading) return <StatusCard title="Faculty dashboard" message="Loading monitored students…" />
  if (error) return <StatusCard title="Faculty dashboard" type="error" message={error instanceof Error ? error.message : 'Unable to load faculty data.'} />
  if (!data) return <StatusCard title="Faculty dashboard" type="empty" message="No faculty data is available." />

  return (
    <section className="dashboard-grid">
      <div className="panel large-panel">
        <div className="panel-header">
          <h2>Faculty profile</h2>
        </div>
        <div className="key-value-grid">
          <div><span>Name</span><strong>{data.profile?.first_name ?? 'Unknown'} {data.profile?.last_name ?? ''}</strong></div>
          <div><span>Employee ID</span><strong>{data.profile?.employee_identifier ?? 'N/A'}</strong></div>
          <div><span>Department</span><strong>{data.profile?.department ?? 'N/A'}</strong></div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>At-risk students</h2>
        </div>
        <div className="stat-number">{data.atRisk?.length ?? 0}</div>
        <p className="helper-text">Students currently classified as at risk.</p>
      </div>

      <div className="panel wide-panel">
        <div className="panel-header split-header">
          <h2>Monitored students</h2>
          <Link to="/faculty/students" className="inline-link">Open list</Link>
        </div>
        {data.students && data.students.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Program</th>
                <th>Latest record</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {data.students.slice(0, 6).map((student) => (
                <tr key={student.id}>
                  <td>
                    <Link to={`/faculty/students/${student.id}`} className="inline-link">
                      {student.first_name ?? 'Unknown'} {student.last_name ?? ''}
                    </Link>
                  </td>
                  <td>{student.program ?? 'N/A'}</td>
                  <td>{student.latest_record_date ? new Date(student.latest_record_date).toLocaleDateString() : 'N/A'}</td>
                  <td>{student.risk_level ?? 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <StatusCard title="No monitored students" type="empty" message="There are no students in the monitored list right now." />
        )}
      </div>
    </section>
  )
}

function FacultyStudentListPage() {
  const { token } = useAuth()
  const { data, isLoading, error } = useQuery({
    queryKey: ['faculty-students', token],
    queryFn: () => facultyApi.students(token ?? undefined),
    enabled: Boolean(token),
  })

  if (isLoading) return <StatusCard title="Students" message="Loading students…" />
  if (error) return <StatusCard title="Students" type="error" message={error instanceof Error ? error.message : 'Unable to load students.'} />

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Student monitor</h2>
      </div>
      {data && data.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Identifier</th>
              <th>Program</th>
              <th>Risk</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {data.map((student) => (
              <tr key={student.id}>
                <td>{student.first_name ?? 'Unknown'} {student.last_name ?? ''}</td>
                <td>{student.student_identifier ?? 'N/A'}</td>
                <td>{student.program ?? 'N/A'}</td>
                <td>{student.risk_level ?? 'N/A'}</td>
                <td>
                  <Link to={`/faculty/students/${student.id}`} className="inline-link">Details</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <StatusCard title="No students" type="empty" message="No monitored students are available for this view." />
      )}
    </section>
  )
}

function FacultyStudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>()
  const { token } = useAuth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['faculty-student', studentId, token],
    queryFn: () => facultyApi.studentDetail(Number(studentId), token ?? undefined),
    enabled: Boolean(token) && Boolean(studentId),
  })

  if (isLoading) return <StatusCard title="Student detail" message="Loading student details…" />
  if (error) return <StatusCard title="Student detail" type="error" message={error instanceof Error ? error.message : 'Unable to load the student detail.'} />
  if (!data) return <StatusCard title="Student detail" type="empty" message="This student profile is not available." />

  return (
    <section className="dashboard-grid">
      <div className="panel large-panel">
        <div className="panel-header">
          <h2>Student detail</h2>
        </div>
        <div className="key-value-grid">
          <div><span>Name</span><strong>{data.first_name ?? 'Unknown'} {data.last_name ?? ''}</strong></div>
          <div><span>Identifier</span><strong>{data.student_identifier ?? 'N/A'}</strong></div>
          <div><span>Program</span><strong>{data.program ?? 'N/A'}</strong></div>
          <div><span>Latest risk</span><strong>{data.risk_level ?? 'N/A'}</strong></div>
        </div>
      </div>

      <div className="panel wide-panel">
        <div className="panel-header">
          <h2>Academic history</h2>
        </div>
        {data.academic_records && data.academic_records.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Created</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {data.academic_records.map((record) => (
                <tr key={record.id}>
                  <td>{record.id}</td>
                  <td>{record.created_at ? new Date(record.created_at).toLocaleString() : 'N/A'}</td>
                  <td>{record.updated_at ? new Date(record.updated_at).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <StatusCard title="No academic records" type="empty" message="No academic records are associated with this student yet." />
        )}
      </div>
    </section>
  )
}

function FacultyAlertsPage() {
  const { token } = useAuth()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['faculty-alerts', token],
    queryFn: () => facultyApi.alerts(token ?? undefined),
    enabled: Boolean(token),
  })

  const { mutate, isPending } = useMutation({
    mutationFn: ({ alertId, status }: { alertId: number; status: AlertRecord['status'] }) =>
      facultyApi.updateAlertStatus(alertId, status, token ?? undefined),
    onSuccess: (updatedAlert) => {
      queryClient.setQueryData<AlertRecord[]>(['faculty-alerts', token], (current) =>
        current
          ? current.map((alert) => (alert.id === updatedAlert.id ? updatedAlert : alert))
          : current,
      )
    },
  })

  if (isLoading) return <StatusCard title="Alerts" message="Loading alerts…" />
  if (error) return <StatusCard title="Alerts" type="error" message={error instanceof Error ? error.message : 'Unable to load alert workflow data.'} />

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Alert workflow</h2>
      </div>
      {data && data.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Student</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {data.map((alert) => (
              <tr key={alert.id}>
                <td>{alert.id}</td>
                <td>{alert.student_id}</td>
                <td>{alert.severity}</td>
                <td>{alert.status}</td>
                <td>{new Date(alert.updated_at).toLocaleString()}</td>
                <td>
                  <select
                    value={alert.status}
                    onChange={(event) =>
                      mutate({ alertId: alert.id, status: event.target.value as AlertRecord['status'] })
                    }
                    disabled={isPending}
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <StatusCard title="No alerts" type="empty" message="No alert records are available for the current filter." />
      )}
    </section>
  )
}

function StatusCard({
  title,
  message,
  type = 'info',
}: {
  title: string
  message: string
  type?: 'info' | 'empty' | 'error'
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      <div className={`status-box status-box--${type}`}>{message}</div>
    </section>
  )
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />

        <Route
          path="/"
          element={
            <RequireAuth>
              <AppShell>
                <Navigate to={getRolePath(useAuth().user?.role)} replace />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/student/dashboard"
          element={
            <RequireAuth roles={['STUDENT']}>
              <AppShell>
                <StudentDashboardPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/student/academic-records"
          element={
            <RequireAuth roles={['STUDENT']}>
              <AppShell>
                <StudentAcademicRecordsPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/faculty/dashboard"
          element={
            <RequireAuth roles={['FACULTY']}>
              <AppShell>
                <FacultyDashboardPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/faculty/students"
          element={
            <RequireAuth roles={['FACULTY']}>
              <AppShell>
                <FacultyStudentListPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/faculty/students/:studentId"
          element={
            <RequireAuth roles={['FACULTY']}>
              <AppShell>
                <FacultyStudentDetailPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route
          path="/faculty/alerts"
          element={
            <RequireAuth roles={['FACULTY']}>
              <AppShell>
                <FacultyAlertsPage />
              </AppShell>
            </RequireAuth>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
