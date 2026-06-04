<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import InstallPrompt from '@/components/InstallPrompt.vue'
import MobileDock from '@/components/MobileDock.vue'
import { usePwaStore } from '@/stores/pwa'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const theme = useThemeStore()
const pwa = usePwaStore()
const isHome = computed(() => route.name === 'home')

theme.hydrate()
pwa.hydrate()
pwa.bindInstallEvents()
</script>

<template>
  <div class="min-h-screen transition-colors duration-300" :class="theme.isDark ? 'theme-dark bg-sdu-night text-white' : 'theme-light bg-[#f6f7fb] text-slate-900'">
    <div v-if="theme.isDark" class="fixed inset-0 -z-10 overflow-hidden">
      <div class="absolute inset-x-0 top-[-16rem] h-[28rem] bg-[radial-gradient(circle_at_top,rgba(241,168,109,0.16),transparent_50%)]"></div>
      <div class="absolute left-[-8rem] top-20 h-72 w-72 rounded-full bg-sdu-royal/20 blur-3xl"></div>
      <div class="absolute bottom-10 right-[-6rem] h-80 w-80 rounded-full bg-sdu-copper/10 blur-3xl"></div>
      <div class="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.03),transparent_30%,rgba(255,255,255,0.02))]"></div>
    </div>

    <AppHeader v-if="!isHome" />

    <main
      class="mx-auto pb-32 lg:pb-20"
      :class="
        isHome
          ? 'min-h-screen max-w-[94rem] px-0 pt-0 sm:pb-36'
          : 'min-h-[calc(100vh-12rem)] max-w-7xl px-4 pt-4 sm:px-6 sm:pt-6 lg:px-8'
      "
    >
      <RouterView />
    </main>

    <AppFooter v-if="!isHome" />
    <MobileDock />
    <InstallPrompt />
  </div>
</template>
