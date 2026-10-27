import { useState } from 'react'

export const label = (s) => String(s).replace(/_/g, ' ')

// Shared async-submit state for every feature form.
export function useSubmit(fn) {
  const [state, setState] = useState({ loading: false, error: null, data: null, mode: null })
  const run = async (...args) => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const { data, mode } = await fn(...args)
      setState({ loading: false, error: null, data, mode })
    } catch (e) {
      setState({ loading: false, error: e.message, data: null, mode: null })
    }
  }
  return [state, run]
}

export const money = (n, currency = 'INR') => {
  try {
    return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(n)
  } catch {
    return `${currency} ${Math.round(n).toLocaleString()}`
  }
}
