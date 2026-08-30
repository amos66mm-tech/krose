import { createContext, useContext, useState, type ReactNode } from 'react'

interface CountryContextValue {
  countryCode: string | undefined
  setCountryCode: (code: string | undefined) => void
}

const CountryContext = createContext<CountryContextValue | undefined>(undefined)

export function CountryProvider({ children }: { children: ReactNode }) {
  const [countryCode, setCountryCode] = useState<string | undefined>(undefined)
  return <CountryContext.Provider value={{ countryCode, setCountryCode }}>{children}</CountryContext.Provider>
}

export function useCountry() {
  const ctx = useContext(CountryContext)
  if (!ctx) throw new Error('useCountry must be used within CountryProvider')
  return ctx
}
