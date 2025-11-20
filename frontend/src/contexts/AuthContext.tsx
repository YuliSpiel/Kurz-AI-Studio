import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { UserResponse, login as apiLogin, register as apiRegister, LoginRequest, RegisterRequest } from '../api/client'

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  isLoading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load auth from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('auth_user')

    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }

    setIsLoading(false)
  }, [])

  const login = async (data: LoginRequest) => {
    const response = await apiLogin(data)

    // Save to state
    setToken(response.access_token)
    setUser(response.user)

    // Save to localStorage
    localStorage.setItem('auth_token', response.access_token)
    localStorage.setItem('auth_user', JSON.stringify(response.user))
  }

  const register = async (data: RegisterRequest) => {
    await apiRegister(data)

    // After registration, login automatically
    await login({
      email: data.email,
      password: data.password,
    })
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
