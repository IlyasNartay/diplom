<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  email: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''

  try {
    const payload = await api.post('/api/auth/login', form)
    auth.setSession(payload)
    router.push(route.query.redirect || '/')
  } catch (err) {
    error.value = err.message || 'Не удалось войти'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-xl">
    <div class="panel p-8 sm:p-10">
      <div class="eyebrow">Sign In</div>
      <h1 class="mt-3 font-display text-4xl text-white">Вход в аккаунт</h1>
      <p class="mt-4 text-sm leading-7 text-sdu-mist/75">
        Используй данные `auth_service`, чтобы покупать билеты, видеть историю и управлять сохранёнными картами.
      </p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Email</label>
          <input v-model="form.email" type="email" class="field" placeholder="student@sdu.edu.kz" required />
        </div>

        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Пароль</label>
          <input v-model="form.password" type="password" class="field" placeholder="••••••••" required />
        </div>

        <div v-if="error" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {{ error }}
        </div>

        <button class="btn-primary w-full" :disabled="loading">
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>

      <p class="mt-6 text-sm text-sdu-mist/75">
        Ещё нет аккаунта?
        <RouterLink class="text-sdu-copper" to="/register">Создать новый</RouterLink>
      </p>
    </div>
  </section>
</template>
