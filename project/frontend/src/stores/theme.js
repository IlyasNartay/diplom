import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const THEME_KEY = 'ticketon-ui-theme'

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

function applyThemeClass(value) {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.classList.toggle('theme-dark', value === 'dark')
  document.documentElement.classList.toggle('theme-light', value === 'light')
  document.documentElement.style.colorScheme = value === 'light' ? 'light' : 'dark'
}

export const useThemeStore = defineStore('theme', () => {
  const theme = ref('dark')

  const isDark = computed(() => theme.value === 'dark')
  const isLight = computed(() => theme.value === 'light')

  function hydrate() {
    theme.value = readThemePreference()
    applyThemeClass(theme.value)
  }

  function setTheme(value) {
    theme.value = value === 'light' ? 'light' : 'dark'
    writeThemePreference(theme.value)
    applyThemeClass(theme.value)
  }

  function toggleTheme() {
    setTheme(isDark.value ? 'light' : 'dark')
  }

  return {
    theme,
    isDark,
    isLight,
    hydrate,
    setTheme,
    toggleTheme
  }
})
