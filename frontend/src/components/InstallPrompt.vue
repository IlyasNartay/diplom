<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const deferredPrompt = ref(null)
const canInstall = ref(false)
const dismissed = ref(false)

function onBeforeInstallPrompt(event) {
  event.preventDefault()
  deferredPrompt.value = event
  canInstall.value = true
}

async function installApp() {
  if (!deferredPrompt.value) {
    return
  }
  deferredPrompt.value.prompt()
  await deferredPrompt.value.userChoice
  deferredPrompt.value = null
  canInstall.value = false
}

function closePrompt() {
  dismissed.value = true
}

onMounted(() => {
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})

onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})
</script>

<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="translate-y-6 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-6 opacity-0"
  >
    <div
      v-if="canInstall && !dismissed"
      class="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-xl rounded-[1.75rem] border border-sdu-copper/30 bg-sdu-ink/95 p-4 shadow-copper backdrop-blur-xl"
    >
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="font-display text-xl text-white">Установить приложение</div>
          <p class="text-sm text-sdu-mist/75">
            Быстрый доступ к афише, билетам и истории бронирований прямо с домашнего экрана.
          </p>
        </div>
        <div class="flex gap-2">
          <button class="btn-secondary px-4 py-2" @click="closePrompt">
            Позже
          </button>
          <button class="btn-primary px-4 py-2" @click="installApp">
            Установить
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
