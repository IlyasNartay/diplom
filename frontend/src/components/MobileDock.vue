<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()

auth.hydrate()
theme.hydrate()

const items = computed(() => {
  const base = [{ label: 'Home', to: '/' }]

  if (!auth.isAuthenticated) {
    return [
      ...base,
      { label: 'Login', to: '/login' },
      { label: 'Join', to: '/register' }
    ]
  }

  return [
    ...base,
    { label: 'History', to: '/history' },
    { label: 'Cards', to: '/cards' },
    ...(auth.user.role === 'admin' ? [{ label: 'Admin', to: '/admin' }] : [])
  ]
})
</script>

<template>
  <nav
    class="mobile-dock fixed inset-x-0 bottom-0 z-50 px-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3 backdrop-blur-2xl md:hidden"
    :class="
      theme.isDark
        ? 'border-t border-white/10 bg-sdu-ink/95'
        : 'border-t border-slate-200 bg-white/95'
    "
  >
    <div class="mx-auto grid max-w-lg gap-2" :class="items.length > 3 ? 'grid-cols-4' : 'grid-cols-3'">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="rounded-2xl border px-3 py-3 text-center text-[0.68rem] uppercase tracking-[0.18em] transition"
        :class="
          route.path === item.to
            ? theme.isDark
              ? 'border-sdu-copper/35 bg-sdu-copper/12 text-sdu-copper'
              : 'border-sdu-copper/35 bg-amber-50 text-sdu-royal'
            : theme.isDark
              ? 'border-white/10 bg-white/5 text-sdu-mist/70'
              : 'border-slate-200 bg-white text-slate-500'
        "
      >
        {{ item.label }}
      </RouterLink>
    </div>
  </nav>
</template>
