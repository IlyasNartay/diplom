<script setup>
import { onMounted, reactive, ref } from 'vue'

import { api } from '@/lib/api'

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
    error.value = err.message || 'Не удалось загрузить карты'
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
    error.value = err.message || 'Не удалось добавить карту'
  } finally {
    saving.value = false
  }
}

async function setDefault(cardId) {
  try {
    await api.patch(`/api/cards/${cardId}/default`, {})
    await loadCards()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить карту'
  }
}

async function removeCard(cardId) {
  try {
    await api.delete(`/api/cards/${cardId}`)
    await loadCards()
  } catch (err) {
    error.value = err.message || 'Не удалось удалить карту'
  }
}

onMounted(loadCards)
</script>

<template>
  <section class="grid gap-6 xl:grid-cols-[0.85fr_1.15fr] xl:gap-8">
    <div class="panel p-5 sm:p-6 lg:p-8">
      <div class="eyebrow">Payment Profile</div>
      <h1 class="mt-3 font-display text-3xl text-white sm:text-4xl">Сохранённые карты</h1>
      <p class="mt-4 text-sm leading-7 text-sdu-mist/75">
        Экран подключён к `payment_service`. Для учебного backend здесь доступны добавление, удаление и смена default-карты.
      </p>

      <form class="mt-6 space-y-4 sm:mt-8" @submit.prevent="addCard">
        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Номер карты</label>
          <input v-model="form.number" class="field" placeholder="4111 1111 1111 1111" required />
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Месяц</label>
            <input v-model="form.exp_month" class="field" inputmode="numeric" placeholder="12" required />
          </div>
          <div>
            <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Год</label>
            <input v-model="form.exp_year" class="field" inputmode="numeric" placeholder="2030" required />
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">CVV</label>
            <input v-model="form.cvv" class="field" inputmode="numeric" placeholder="123" required />
          </div>
          <div>
            <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Держатель</label>
            <input v-model="form.holder_name" class="field" placeholder="SDU STUDENT" required />
          </div>
        </div>

        <label class="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-sdu-mist/80">
          <input v-model="form.is_default" type="checkbox" class="h-4 w-4 accent-[#f1a86d]" />
          Сделать основной картой
        </label>

        <button class="btn-primary w-full" :disabled="saving">
          {{ saving ? 'Сохраняем...' : 'Добавить карту' }}
        </button>
      </form>
    </div>

    <div class="space-y-4">
      <div v-if="error" class="panel p-5 text-sm text-rose-200">
        {{ error }}
      </div>

      <div v-if="loading" class="space-y-4">
        <div
          v-for="index in 3"
          :key="index"
          class="panel h-36 animate-shimmer bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%]"
        ></div>
      </div>

      <div v-else-if="!cards.length" class="panel p-6 text-center sm:p-8">
        <div class="font-display text-3xl text-white">Карты пока не добавлены</div>
        <p class="mt-3 text-sm text-sdu-mist/75">Первая сохранённая карта станет хорошим тестом интеграции с payment API.</p>
      </div>

      <article
        v-for="card in cards"
        :key="card.id"
        class="panel overflow-hidden"
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
              {{ card.is_default ? 'Основная' : 'Card' }}
            </span>
          </div>
          <div class="mt-6 text-sm text-sdu-mist/75 sm:mt-8">Expires {{ card.exp_month }}/{{ card.exp_year }}</div>
        </div>

        <div class="flex flex-col gap-3 p-4 sm:flex-row sm:p-5">
          <button class="btn-secondary flex-1" @click="setDefault(card.id)">
            Сделать основной
          </button>
          <button class="btn-secondary flex-1 border-rose-400/30 text-rose-200 hover:bg-rose-500/10" @click="removeCard(card.id)">
            Удалить
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
