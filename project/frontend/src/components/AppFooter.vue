<script setup>
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
theme.hydrate()
</script>

<template>
  <footer
    class="border-t transition-colors duration-300"
    :class="theme.isDark ? 'border-white/10 bg-black/20' : 'border-slate-200 bg-white/90'"
  >
    <div class="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8" :class="theme.isDark ? 'text-sdu-mist/75' : 'text-slate-600'">
      <div class="flex items-center gap-4">
        <img
          src="/branding/logo_sdu.png"
          alt="SDU University"
          class="h-14 w-auto object-contain opacity-90"
        />
        <div>
          <div class="font-display text-lg" :class="theme.isDark ? 'text-white' : 'text-slate-900'">High-Load Ticket Booking System</div>
          <div>Academic event experience powered by the microservice backend.</div>
        </div>
      </div>
      <div class="flex flex-wrap gap-4 text-xs uppercase tracking-[0.24em]" :class="theme.isDark ? 'text-sdu-copper/75' : 'text-emerald-700'">
        <span>PWA Ready</span>
        <span>Vue 3</span>
        <span>Tailwind CSS</span>
      </div>
    </div>
  </footer>
</template>
