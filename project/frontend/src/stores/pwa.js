import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const PWA_DISMISSED_AT_KEY = 'ticketon-pwa-install-dismissed-at'
export const PWA_DISMISS_REASON_KEY = 'ticketon-pwa-install-dismiss-reason'
export const PWA_INSTALLED_KEY = 'ticketon-pwa-installed'

const SESSION_DISMISS_MS = 1000 * 60 * 30
const PERSISTENT_DISMISS_MS = 1000 * 60 * 60 * 24 * 7

function isStandaloneMode() {
  if (typeof window === 'undefined') {
    return false
  }

  return window.matchMedia?.('(display-mode: standalone)')?.matches || window.navigator.standalone === true
}

function isMobileViewport() {
  if (typeof window === 'undefined') {
    return false
  }

  return window.matchMedia?.('(max-width: 767px)')?.matches ?? false
}

function isIosDevice() {
  if (typeof window === 'undefined') {
    return false
  }

  const ua = window.navigator.userAgent || window.navigator.vendor || ''
  return /iPad|iPhone|iPod/.test(ua) || (ua.includes('Mac') && 'ontouchend' in document)
}

function isSafariBrowser() {
  if (typeof window === 'undefined') {
    return false
  }

  const ua = window.navigator.userAgent || ''
  return /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS/.test(ua)
}

function persistFlag(key, value) {
  if (typeof window === 'undefined') {
    return
  }

  if (value) {
    window.localStorage.setItem(key, '1')
  } else {
    window.localStorage.removeItem(key)
  }
}

export const usePwaStore = defineStore('pwa', () => {
  const deferredPrompt = ref(null)
  const canInstall = ref(false)
  const dismissed = ref(false)
  const dismissedAt = ref(0)
  const dismissReason = ref('')
  const installed = ref(false)
  const listenersBound = ref(false)
  const manualOpen = ref(false)
  const installHint = ref('')

  const isMobile = computed(() => isMobileViewport())
  const isIos = computed(() => isIosDevice())
  const isSafari = computed(() => isSafariBrowser())
  const canShowIosInstallHint = computed(
    () => isIos.value && isSafari.value && !installed.value
  )
  const canShowInstallPrompt = computed(
    () => Boolean(deferredPrompt.value) && !installed.value
  )
  const shouldShowInstallUi = computed(
    () =>
      !installed.value &&
      (manualOpen.value ||
        (!dismissed.value && (canInstall.value || canShowIosInstallHint.value)))
  )

  function dismissTtl() {
    return dismissReason.value === 'later' ? SESSION_DISMISS_MS : PERSISTENT_DISMISS_MS
  }

  function isDismissExpired() {
    if (!dismissed.value || !dismissedAt.value) {
      return true
    }

    return Date.now() - dismissedAt.value >= dismissTtl()
  }

  function persistDismissState() {
    if (typeof window === 'undefined') {
      return
    }

    if (dismissed.value && dismissedAt.value > 0) {
      window.localStorage.setItem(PWA_DISMISSED_AT_KEY, String(dismissedAt.value))

      if (dismissReason.value) {
        window.localStorage.setItem(PWA_DISMISS_REASON_KEY, dismissReason.value)
      } else {
        window.localStorage.removeItem(PWA_DISMISS_REASON_KEY)
      }
    } else {
      window.localStorage.removeItem(PWA_DISMISSED_AT_KEY)
      window.localStorage.removeItem(PWA_DISMISS_REASON_KEY)
    }
  }

  function clearDismissState() {
    dismissed.value = false
    dismissedAt.value = 0
    dismissReason.value = ''
    persistDismissState()
  }

  function markInstalled() {
    installed.value = true
    canInstall.value = false
    deferredPrompt.value = null
    manualOpen.value = false
    installHint.value = ''
    clearDismissState()
    persistFlag(PWA_INSTALLED_KEY, true)
  }

  function syncInstallAvailability() {
    if (installed.value) {
      canInstall.value = false
      return
    }

    if (dismissed.value && isDismissExpired()) {
      clearDismissState()
    }

    canInstall.value = Boolean(deferredPrompt.value) && !dismissed.value
  }

  function onBeforeInstallPrompt(event) {
    event.preventDefault()
    deferredPrompt.value = event
    syncInstallAvailability()
  }

  function onAppInstalled() {
    markInstalled()
  }

  function hydrate() {
    if (typeof window === 'undefined') {
      return
    }

    installed.value = isStandaloneMode()
    if (installed.value) {
      persistFlag(PWA_INSTALLED_KEY, true)
      canInstall.value = false
      clearDismissState()
      return
    }

    persistFlag(PWA_INSTALLED_KEY, false)
    dismissedAt.value = Number(window.localStorage.getItem(PWA_DISMISSED_AT_KEY) || '0')
    dismissReason.value = window.localStorage.getItem(PWA_DISMISS_REASON_KEY) || ''
    dismissed.value = dismissedAt.value > 0
    syncInstallAvailability()
  }

  function bindInstallEvents() {
    if (typeof window === 'undefined' || listenersBound.value) {
      return
    }

    listenersBound.value = true

    if (isStandaloneMode()) {
      markInstalled()
    }

    window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
    window.addEventListener('appinstalled', onAppInstalled)
  }

  async function installApp() {
    installHint.value = ''

    if (installed.value) {
      return false
    }

    if (!deferredPrompt.value) {
      installHint.value =
        'Браузер пока не предложил установку. Открой меню браузера и выбери «Установить приложение».'
      manualOpen.value = true
      return false
    }

    try {
      await deferredPrompt.value.prompt()
      const choiceResult = await deferredPrompt.value.userChoice
      const accepted = choiceResult?.outcome === 'accepted'

      if (accepted) {
        markInstalled()
      } else {
        dismissInstallPrompt('later')
      }

      deferredPrompt.value = null
      syncInstallAvailability()
      return accepted
    } catch {
      installHint.value = 'Не удалось открыть диалог установки. Попробуй через меню браузера.'
      manualOpen.value = true
      return false
    }
  }

  function openInstallUi() {
    if (installed.value) {
      return
    }

    installHint.value = ''
    manualOpen.value = true

    if (dismissed.value && isDismissExpired()) {
      clearDismissState()
    }

    syncInstallAvailability()
  }

  function handleInstallAction() {
    if (installed.value) {
      return
    }

    openInstallUi()

    if (canShowIosInstallHint.value) {
      installHint.value = 'На iPhone/iPad: нажми Share, затем «Add to Home Screen».'
      return
    }

    if (deferredPrompt.value) {
      void installApp()
      return
    }

    installHint.value =
      'Установка появится в меню браузера (Chrome/Edge). Если кнопка не сработала — используй пункт «Установить приложение» в меню ⋮.'
  }

  function dismissInstallPrompt(reason = 'persistent') {
    dismissed.value = true
    dismissedAt.value = Date.now()
    dismissReason.value = reason
    manualOpen.value = false
    installHint.value = ''
    syncInstallAvailability()
    persistDismissState()
  }

  function snoozeInstallPrompt() {
    dismissInstallPrompt('later')
  }

  function resetInstallState() {
    clearDismissState()
    installed.value = false
    manualOpen.value = false
    installHint.value = ''
    syncInstallAvailability()
    persistFlag(PWA_INSTALLED_KEY, false)
  }

  return {
    canInstall,
    canShowInstallPrompt,
    canShowIosInstallHint,
    dismissed,
    dismissedAt,
    dismissReason,
    installed,
    installHint,
    isMobile,
    isIos,
    isSafari,
    manualOpen,
    shouldShowInstallUi,
    hydrate,
    bindInstallEvents,
    installApp,
    openInstallUi,
    handleInstallAction,
    dismissInstallPrompt,
    snoozeInstallPrompt,
    resetInstallState
  }
})
