<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/lib/api'

const router = useRouter()

const form = reactive({
  full_name: '',
  email: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true
  error.value = ''

  try {
    await api.post('/api/auth/register', form)
    router.push({
      name: 'login',
      query: { email: form.email }
    })
  } catch (err) {
    error.value = err.message || 'Не удалось зарегистрироваться'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-xl">
    <div class="panel p-8 sm:p-10">
      <div class="eyebrow">Registration</div>
      <h1 class="mt-3 font-display text-4xl text-white">Создать аккаунт</h1>
      <p class="mt-4 text-sm leading-7 text-sdu-mist/75">
        Новый пользователь сможет авторизоваться через `api_gateway` и участвовать в полном ticket flow.
      </p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Полное имя</label>
          <input v-model="form.full_name" type="text" class="field" placeholder="Aruzhan Student" required />
        </div>

        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Email</label>
          <input v-model="form.email" type="email" class="field" placeholder="student@sdu.edu.kz" required />
        </div>

        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Пароль</label>
          <input v-model="form.password" type="password" class="field" placeholder="Минимум один надёжный пароль" required />
        </div>

        <div v-if="error" class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {{ error }}
        </div>

        <button class="btn-primary w-full" :disabled="loading">
          {{ loading ? 'Создаём аккаунт...' : 'Зарегистрироваться' }}
        </button>
      </form>
    </div>
  </section>
</template>
