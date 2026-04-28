import { computed, ref } from 'vue'

export const LANGUAGE_KEY = 'ticketon-ui-language'

const language = ref('ru')

export function readLanguagePreference() {
  if (typeof window === 'undefined') {
    return 'ru'
  }

  try {
    const raw = window.localStorage.getItem(LANGUAGE_KEY)
    if (raw === 'ru' || raw === 'en') {
      return raw
    }
  } catch {
    // Ignore storage failures.
  }

  return 'ru'
}

export function writeLanguagePreference(value) {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(LANGUAGE_KEY, value)
}

export function useLanguageStore() {
  const isRussian = computed(() => language.value === 'ru')

  function hydrate() {
    language.value = readLanguagePreference()
  }

  function setLanguage(value) {
    language.value = value === 'en' ? 'en' : 'ru'
    writeLanguagePreference(language.value)
  }

  function toggleLanguage() {
    setLanguage(isRussian.value ? 'en' : 'ru')
  }

  return {
    language,
    isRussian,
    hydrate,
    setLanguage,
    toggleLanguage
  }
}
