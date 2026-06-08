<script setup>
import { usePwaStore } from '@/stores/pwa'

const pwa = usePwaStore()
</script>

<template>
  <Transition
    enter-active-class="transition duration-400 ease-out"
    enter-from-class="translate-y-10 scale-95 opacity-0"
    enter-to-class="translate-y-0 scale-100 opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="translate-y-0 scale-100 opacity-100"
    leave-to-class="translate-y-10 scale-95 opacity-0"
  >
    <div
      v-if="pwa.shouldShowInstallUi"
      class="fixed inset-x-4 bottom-[calc(5.5rem+env(safe-area-inset-bottom))] z-[60] mx-auto max-w-md md:bottom-4"
    >
      <div class="overflow-hidden rounded-[1.6rem] border border-sdu-copper/20 bg-[#0b1020]/96 shadow-[0_24px_90px_rgba(0,0,0,0.45)] backdrop-blur-xl">
        <div class="h-1 w-full bg-gradient-to-r from-sdu-royal via-sdu-copper to-emerald-400"></div>

        <div class="p-4">
          <div class="flex items-start gap-3">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/5 p-2">
              <img src="/branding/logo_sdu.png" alt="SDU" class="h-full w-full object-contain" />
            </div>

            <div class="min-w-0 flex-1">
              <div class="text-[0.68rem] font-semibold uppercase tracking-[0.3em] text-sdu-copper/80">PWA</div>
              <div class="mt-1 text-lg font-semibold text-white">Install HLTB</div>
              <p v-if="!pwa.canShowIosInstallHint" class="mt-1 text-sm leading-6 text-sdu-mist/80">
                Добавь на домашний экран для быстрого доступа к афише и билетам.
              </p>
              <p v-else class="mt-1 text-sm leading-6 text-sdu-mist/80">
                На iPhone и iPad нажми Share, затем выбери Add to Home Screen.
              </p>
            </div>

            <button
              type="button"
              class="rounded-full border border-white/10 p-2 text-sdu-mist transition hover:bg-white/10 hover:text-white"
              aria-label="Close install prompt"
              @click.stop="pwa.dismissInstallPrompt('persistent')"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6 6 18"></path>
                <path d="m6 6 12 12"></path>
              </svg>
            </button>
          </div>

          <div class="mt-4 flex gap-2">
            <button class="btn-secondary flex-1 px-4 py-2.5 text-sm" @click.stop="pwa.snoozeInstallPrompt()">
              Позже
            </button>
            <button
              v-if="!pwa.canShowIosInstallHint"
              class="btn-primary flex-1 px-4 py-2.5 text-sm"
              data-install-pwa
              @click="pwa.installApp()"
            >
              Установить
            </button>
            <button
              v-else
              class="btn-primary flex-1 px-4 py-2.5 text-sm"
              @click.stop="pwa.dismissInstallPrompt('persistent')"
            >
              Понятно
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>
