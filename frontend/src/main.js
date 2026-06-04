import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { registerSW } from 'virtual:pwa-register'

import App from './App.vue'
import router from './router'
import './styles.css'

const updateSW = registerSW({
  immediate: true,
  onNeedRefresh() {
    updateSW(true)
  },
  onOfflineReady() {
    console.info('HLTB PWA is ready for offline usage.')
  }
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
