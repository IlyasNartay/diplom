<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/lib/api'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const language = useLanguageStore()
const theme = useThemeStore()
const router = useRouter()

const isDark = computed(() => theme.isDark)

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      eyebrow: 'Регистрация',
      title: 'Создать аккаунт',
      intro:
        'Новый пользователь проходит через api_gateway и может участвовать в полном ticket flow.',
      fullName: 'Полное имя',
      email: 'Email',
      password: 'Пароль',
      passwordPh: 'Надёжный пароль',
      creating: 'Создаём аккаунт...',
      submit: 'Зарегистрироваться',
      loadError: 'Не удалось зарегистрироваться'
    }
  }
  return {
    eyebrow: 'Registration',
    title: 'Create an account',
    intro: 'New users sign in through the API gateway and can run the full ticket purchase flow.',
    fullName: 'Full name',
    email: 'Email',
    password: 'Password',
    passwordPh: 'Strong password',
    creating: 'Creating account…',
    submit: 'Register',
    loadError: 'Could not register'
  }
})

const panelClass = computed(() =>
  isDark.value
    ? 'panel p-8 sm:p-10'
    : 'rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_28px_90px_rgba(15,23,42,0.08)] sm:p-10'
)

const eyebrowClass = computed(() =>
  isDark.value ? 'eyebrow' : 'text-xs uppercase tracking-[0.34em] text-emerald-700'
)

const titleClass = computed(() =>
  isDark.value ? 'mt-3 font-display text-4xl text-white' : 'mt-3 font-display text-4xl text-slate-900'
)

const introClass = computed(() =>
  isDark.value ? 'mt-4 text-sm leading-7 text-sdu-mist/75' : 'mt-4 text-sm leading-7 text-slate-600'
)

const labelClass = computed(() =>
  isDark.value ? 'mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65' : 'mb-2 block text-xs uppercase tracking-[0.24em] text-slate-500'
)

const fieldClass = computed(() =>
  isDark.value
    ? 'field'
    : 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-sdu-copper/70 focus:bg-white'
)

const errorBoxClass = computed(() =>
  isDark.value
    ? 'rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200'
    : 'rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800'
)

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
    error.value = err.message || t.value.loadError
  } finally {
    loading.value = false
  }
}

language.hydrate()
theme.hydrate()
</script>

<template>
  <section class="mx-auto max-w-xl">
    <div :class="panelClass">
      <div :class="eyebrowClass">{{ t.eyebrow }}</div>
      <h1 :class="titleClass">{{ t.title }}</h1>
      <p :class="introClass">
        {{ t.intro }}
      </p>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label :class="labelClass">{{ t.fullName }}</label>
          <input v-model="form.full_name" type="text" :class="fieldClass" placeholder="Aruzhan Student" required />
        </div>

        <div>
          <label :class="labelClass">{{ t.email }}</label>
          <input v-model="form.email" type="email" :class="fieldClass" placeholder="student@sdu.edu.kz" required />
        </div>

        <div>
          <label :class="labelClass">{{ t.password }}</label>
          <input v-model="form.password" type="password" :class="fieldClass" :placeholder="t.passwordPh" required />
        </div>

        <div v-if="error" :class="errorBoxClass">
          {{ error }}
        </div>

        <button class="btn-primary w-full" :disabled="loading">
          {{ loading ? t.creating : t.submit }}
        </button>
      </form>
    </div>
  </section>
</template>
