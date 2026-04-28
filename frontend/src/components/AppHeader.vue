<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const theme = useThemeStore()
const language = useLanguageStore()

auth.hydrate()
theme.hydrate()
language.hydrate()

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      poster: 'Афиша',
      history: 'История',
      cards: 'Карты',
      login: 'Войти',
      register: 'Регистрация',
      signOut: 'Выйти',
      admin: 'Admin'
    }
  }

  return {
    poster: 'Events',
    history: 'History',
    cards: 'Cards',
    login: 'Sign in',
    register: 'Register',
    signOut: 'Sign out',
    admin: 'Admin'
  }
})

const navItems = computed(() => [
  { label: t.value.poster, to: '/' },
  ...(auth.isAuthenticated ? [{ label: t.value.history, to: '/history' }, { label: t.value.cards, to: '/cards' }] : []),
  ...(auth.user.role === 'admin' ? [{ label: t.value.admin, to: '/admin' }] : [])
])

function signOut() {
  auth.logout()
  if (route.meta.requiresAuth) {
    router.push('/')
  }
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b backdrop-blur-2xl transition-colors duration-300" :class="theme.isDark.value ? 'border-white/10 bg-sdu-night/70' : 'border-slate-200 bg-white/90'">
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-2 px-4 py-3 sm:gap-3 sm:px-6 sm:py-4 lg:px-8">
      <RouterLink to="/" class="flex min-w-0 items-center gap-3 sm:gap-4">
        <img
          src="/branding/logo_sdu.png"
          alt="SDU University"
          class="h-10 w-auto shrink-0 object-contain sm:h-14"
        />
        <div class="hidden min-w-0 sm:block">
          <div class="truncate font-display text-xl tracking-[0.12em]" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">High-Load Ticket Booking System</div>
          <div class="text-[0.68rem] uppercase tracking-[0.38em]" :class="theme.isDark.value ? 'text-sdu-copper/80' : 'text-emerald-700'">Microservices architecture</div>
        </div>
      </RouterLink>

      <nav class="hidden items-center gap-2 md:flex">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="rounded-full px-4 py-2 text-sm transition"
          :class="[
            theme.isDark.value ? 'text-sdu-mist/80 hover:bg-white/5 hover:text-white' : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900',
            route.path === item.to
              ? theme.isDark.value
                ? 'bg-white/10 text-white'
                : 'bg-slate-900 text-white'
              : ''
          ]"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="flex shrink-0 items-center gap-2">
        <button
          type="button"
          class="hidden h-10 w-10 items-center justify-center rounded-full border transition sm:inline-flex"
          :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-white hover:bg-white/10' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'"
          @click="theme.toggleTheme()"
        >
          <svg v-if="theme.isDark.value" viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="4"></circle>
            <path d="M12 2v2.5"></path>
            <path d="M12 19.5V22"></path>
            <path d="m4.93 4.93 1.77 1.77"></path>
            <path d="m17.3 17.3 1.77 1.77"></path>
            <path d="M2 12h2.5"></path>
            <path d="M19.5 12H22"></path>
            <path d="m4.93 19.07 1.77-1.77"></path>
            <path d="m17.3 6.7 1.77-1.77"></path>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor">
            <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 1 0 9.8 9.8Z"></path>
          </svg>
        </button>

        <button
          type="button"
          class="hidden rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] transition sm:inline-flex"
          :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-white hover:bg-white/10' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'"
          @click="language.toggleLanguage()"
        >
          {{ language.isRussian.value ? 'EN' : 'RU' }}
        </button>

        <template v-if="auth.isAuthenticated">
          <span class="hidden rounded-full border px-4 py-2 text-xs uppercase tracking-[0.24em] sm:inline-flex" :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-sdu-copper/80' : 'border-slate-200 bg-slate-50 text-emerald-700'">
            {{ auth.user.role }}
          </span>
          <button class="btn-secondary px-3 py-2 text-xs sm:px-4 sm:text-sm" @click="signOut">
            {{ t.signOut }}
          </button>
        </template>
        <template v-else>
          <RouterLink class="btn-secondary px-3 py-2 text-xs sm:px-4 sm:text-sm" to="/login">
            {{ t.login }}
          </RouterLink>
          <RouterLink class="btn-primary hidden px-4 py-2 text-sm sm:inline-flex" to="/register">
            {{ t.register }}
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>


