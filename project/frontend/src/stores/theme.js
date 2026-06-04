import { computed, ref } from 'vue'

export const THEME_KEY = 'ticketon-ui-theme'

const theme = ref('dark')

export function readThemePreference() {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  try {
    const raw = window.localStorage.getItem(THEME_KEY)
    if (raw === 'light' || raw === 'dark') {
      return raw
    }
  } catch {
    // Ignore storage failures and fall back to system defaults.
  }

  return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export function writeThemePreference(value) {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(THEME_KEY, value)
}

export function useThemeStore() {
  const isDark = computed(() => theme.value === 'dark')

  function hydrate() {
    theme.value = readThemePreference()
  }

  function setTheme(value) {
    theme.value = value === 'light' ? 'light' : 'dark'
    writeThemePreference(theme.value)
  }

  function toggleTheme() {
    setTheme(isDark.value ? 'light' : 'dark')
  }

  return {
    theme,
    isDark,
    hydrate,
    setTheme,
    toggleTheme
  }
}
