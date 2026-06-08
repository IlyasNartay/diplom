<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { api } from '@/lib/api'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const language = useLanguageStore()
const theme = useThemeStore()

const isDark = computed(() => theme.isDark)

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      eyebrow: 'Платёжный профиль',
      title: 'Сохранённые карты',
      intro:
        'Подключено к payment_service: добавление, удаление и карта по умолчанию (учебный backend).',
      cardNumber: 'Номер карты',
      month: 'Месяц',
      year: 'Год',
      cvv: 'CVV',
      holder: 'Держатель',
      defaultCheck: 'Сделать основной картой',
      saving: 'Сохраняем...',
      addCard: 'Добавить карту',
      loadListError: 'Не удалось загрузить карты',
      addError: 'Не удалось добавить карту',
      updateError: 'Не удалось обновить карту',
      deleteError: 'Не удалось удалить карту',
      emptyTitle: 'Карты пока не добавлены',
      emptyText: 'Первая сохранённая карта — хороший тест интеграции с payment API.',
      defaultBadge: 'Основная',
      otherBadge: 'Дополнительная',
      expires: 'Действует до',
      setDefault: 'Сделать основной',
      remove: 'Удалить'
    }
  }
  return {
    eyebrow: 'Payment profile',
    title: 'Saved cards',
    intro: 'Connected to payment_service: add, remove, and set a default card (demo backend).',
    cardNumber: 'Card number',
    month: 'Month',
    year: 'Year',
    cvv: 'CVV',
    holder: 'Cardholder',
    defaultCheck: 'Set as default card',
    saving: 'Saving…',
    addCard: 'Add card',
    loadListError: 'Could not load cards',
    addError: 'Could not add card',
    updateError: 'Could not update card',
    deleteError: 'Could not remove card',
    emptyTitle: 'No cards yet',
    emptyText: 'Saving your first card is a good end-to-end test of the payment API.',
    defaultBadge: 'Default',
    otherBadge: 'Other',
    expires: 'Expires',
    setDefault: 'Set default',
    remove: 'Remove'
  }
})

const leftPanelClass = computed(() =>
  isDark.value
    ? 'panel p-5 sm:p-6 lg:p-8'
    : 'rounded-[2rem] border border-slate-200 bg-white p-5 shadow-[0_28px_90px_rgba(15,23,42,0.08)] sm:p-6 lg:p-8'
)

const eyebrowClass = computed(() =>
  isDark.value ? 'eyebrow' : 'text-xs uppercase tracking-[0.34em] text-emerald-700'
)

const titleClass = computed(() =>
  isDark.value
    ? 'mt-3 font-display text-3xl text-white sm:text-4xl'
    : 'mt-3 font-display text-3xl text-slate-900 sm:text-4xl'
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

const checkRowClass = computed(() =>
  isDark.value
    ? 'flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-sdu-mist/80'
    : 'flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700'
)

const errorPanelClass = computed(() =>
  isDark.value ? 'panel p-5 text-sm text-rose-200' : 'rounded-[2rem] border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800'
)

const shimmerClass = computed(() =>
  isDark.value
    ? 'panel h-36 animate-shimmer bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%]'
    : 'h-36 rounded-[2rem] border border-slate-200 bg-[linear-gradient(90deg,rgba(241,245,249,1),rgba(255,255,255,1),rgba(241,245,249,1))] bg-[length:200%_100%] animate-shimmer'
)

const emptyPanelClass = computed(() =>
  isDark.value ? 'panel p-6 text-center sm:p-8' : 'rounded-[2rem] border border-slate-200 bg-white p-6 text-center shadow-sm sm:p-8'
)

const emptyTitleClass = computed(() =>
  isDark.value ? 'font-display text-3xl text-white' : 'font-display text-3xl text-slate-900'
)

const cardShellClass = computed(() =>
  isDark.value ? 'panel overflow-hidden' : 'overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm'
)

const removeBtnClass = computed(() =>
  isDark.value
    ? 'btn-secondary flex-1 border-rose-400/30 text-rose-200 hover:bg-rose-500/10'
    : 'btn-secondary flex-1 border-rose-200 text-rose-700 hover:bg-rose-50'
)

const cards = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')

const form = reactive({
  number: '',
  exp_month: '',
  exp_year: '',
  cvv: '',
  holder_name: '',
  is_default: true
})

async function loadCards() {
  loading.value = true
  error.value = ''

  try {
    cards.value = await api.get('/api/cards')
  } catch (err) {
    error.value = err.message || t.value.loadListError
  } finally {
    loading.value = false
  }
}

async function addCard() {
  saving.value = true
  error.value = ''

  try {
    await api.post('/api/cards', {
      ...form,
      exp_month: Number(form.exp_month),
      exp_year: Number(form.exp_year)
    })
    form.number = ''
    form.exp_month = ''
    form.exp_year = ''
    form.cvv = ''
    form.holder_name = ''
    form.is_default = false
    await loadCards()
  } catch (err) {
    error.value = err.message || t.value.addError
  } finally {
    saving.value = false
  }
}

async function setDefault(cardId) {
  try {
    await api.patch(`/api/cards/${cardId}/default`, {})
    await loadCards()
  } catch (err) {
    error.value = err.message || t.value.updateError
  }
}

async function removeCard(cardId) {
  try {
    await api.delete(`/api/cards/${cardId}`)
    await loadCards()
  } catch (err) {
    error.value = err.message || t.value.deleteError
  }
}

onMounted(() => {
  language.hydrate()
  theme.hydrate()
  loadCards()
})
</script>

<template>
  <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr] xl:gap-8">
    <div :class="leftPanelClass">
      <div :class="eyebrowClass">{{ t.eyebrow }}</div>
      <h1 :class="titleClass">{{ t.title }}</h1>
      <p :class="introClass">
        {{ t.intro }}
      </p>

      <form class="mt-6 space-y-4 sm:mt-8" @submit.prevent="addCard">
        <div>
          <label :class="labelClass">{{ t.cardNumber }}</label>
          <input v-model="form.number" :class="fieldClass" placeholder="4111 1111 1111 1111" required />
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label :class="labelClass">{{ t.month }}</label>
            <input v-model="form.exp_month" :class="fieldClass" inputmode="numeric" placeholder="12" required />
          </div>
          <div>
            <label :class="labelClass">{{ t.year }}</label>
            <input v-model="form.exp_year" :class="fieldClass" inputmode="numeric" placeholder="2030" required />
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label :class="labelClass">{{ t.cvv }}</label>
            <input v-model="form.cvv" :class="fieldClass" inputmode="numeric" placeholder="123" required />
          </div>
          <div>
            <label :class="labelClass">{{ t.holder }}</label>
            <input v-model="form.holder_name" :class="fieldClass" placeholder="SDU STUDENT" required />
          </div>
        </div>

        <label :class="checkRowClass">
          <input v-model="form.is_default" type="checkbox" class="h-4 w-4 accent-[#f1a86d]" />
          {{ t.defaultCheck }}
        </label>

        <button class="btn-primary w-full" :disabled="saving">
          {{ saving ? t.saving : t.addCard }}
        </button>
      </form>
    </div>

    <div class="space-y-4">
      <div v-if="error" :class="errorPanelClass">
        {{ error }}
      </div>

      <div v-if="loading" class="space-y-4">
        <div
          v-for="index in 3"
          :key="index"
          :class="shimmerClass"
        ></div>
      </div>

      <div v-else-if="!cards.length" :class="emptyPanelClass">
        <div :class="emptyTitleClass">{{ t.emptyTitle }}</div>
        <p :class="introClass" class="mt-3">{{ t.emptyText }}</p>
      </div>

      <article
        v-for="card in cards"
        :key="card.id"
        :class="cardShellClass"
      >
        <div class="bg-[linear-gradient(135deg,rgba(44,50,121,0.94),rgba(9,11,24,1))] p-5 sm:p-6">
          <div class="flex items-start justify-between gap-4">
            <div>
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">{{ card.brand }}</div>
              <div class="mt-4 font-display text-2xl text-white sm:text-3xl">•••• •••• •••• {{ card.last4 }}</div>
              <div class="mt-2 text-sm uppercase tracking-[0.22em] text-sdu-mist/65">
                {{ card.holder_name }}
              </div>
            </div>
            <span
              class="rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em]"
              :class="card.is_default ? 'border-sdu-copper/40 bg-sdu-copper/15 text-sdu-copper' : 'border-white/10 bg-white/5 text-sdu-mist/70'"
            >
              {{ card.is_default ? t.defaultBadge : t.otherBadge }}
            </span>
          </div>
          <div class="mt-6 text-sm text-sdu-mist/75 sm:mt-8">
            {{ t.expires }} {{ card.exp_month }}/{{ card.exp_year }}
          </div>
        </div>

        <div class="flex flex-col gap-3 p-4 sm:flex-row sm:p-5">
          <button class="btn-secondary flex-1" @click="setDefault(card.id)">
            {{ t.setDefault }}
          </button>
          <button :class="removeBtnClass" @click="removeCard(card.id)">
            {{ t.remove }}
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
