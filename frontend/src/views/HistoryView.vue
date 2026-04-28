<script setup>
import { onMounted, ref } from 'vue'

import StatusBadge from '@/components/StatusBadge.vue'
import { API_BASE_URL, api } from '@/lib/api'
import { formatDateTime, normalizeAssetUrl } from '@/lib/format'

const history = ref([])
const loading = ref(true)
const error = ref('')

async function loadHistory() {
  loading.value = true
  error.value = ''

  try {
    history.value = await api.get('/api/history/me')
  } catch (err) {
    error.value = err.message || 'Не удалось получить историю бронирований'
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<template>
  <section>
    <div class="mb-5 sm:mb-6">
      <div class="eyebrow">Booking Archive</div>
      <h1 class="mt-3 font-display text-3xl text-white sm:text-4xl">История бронирований</h1>
      <p class="mt-4 max-w-2xl text-sm leading-7 text-sdu-mist/75">
        Здесь отображаются записи из `orchestrator`, включая итоговый статус, билет и признаки того, что событие уже прошло.
      </p>
    </div>

    <div v-if="error" class="panel p-5 text-sm text-rose-200">
      {{ error }}
    </div>

    <div v-else-if="loading" class="space-y-4">
      <div
        v-for="index in 3"
        :key="index"
        class="panel h-40 animate-shimmer bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%]"
      ></div>
    </div>

    <div v-else-if="!history.length" class="panel p-6 text-center sm:p-8">
      <div class="font-display text-3xl text-white">Пока пусто</div>
      <p class="mt-3 text-sm text-sdu-mist/75">После первой покупки здесь появятся статусы и ссылки на билеты.</p>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="booking in history"
        :key="booking.booking_id"
        class="panel grid gap-4 p-5 sm:gap-6 sm:p-8 lg:grid-cols-[1.4fr_0.6fr]"
      >
        <div>
          <div class="flex flex-wrap items-center gap-3">
            <StatusBadge :status="booking.status" />
            <span class="text-xs uppercase tracking-[0.2em] text-sdu-mist/60">
              {{ formatDateTime(booking.created_at) }}
            </span>
          </div>

          <h2 class="mt-4 font-display text-2xl text-white sm:text-3xl">
            {{ booking.event_title || 'Мероприятие без названия' }}
          </h2>

          <p class="mt-3 break-all text-sm leading-7 text-sdu-mist/75">
            Booking ID: {{ booking.booking_id }}
          </p>

          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="seatId in booking.seat_ids"
              :key="seatId"
              class="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-sdu-mist/80"
            >
              {{ seatId }}
            </span>
          </div>

          <p v-if="booking.error_reason" class="mt-4 text-sm text-rose-200">
            {{ booking.error_reason }}
          </p>
        </div>

        <div class="flex flex-col justify-between gap-4 rounded-[1.35rem] border border-white/10 bg-white/5 p-4 sm:rounded-[1.6rem] sm:p-5">
          <div>
            <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Состояние события</div>
            <div class="mt-3 space-y-2 text-sm text-sdu-mist/75">
              <div>Активно: {{ booking.event_is_active ? 'Да' : 'Нет' }}</div>
              <div>Сеанс прошёл: {{ booking.session_has_passed ? 'Да' : 'Нет' }}</div>
            </div>
          </div>

          <a
            v-if="booking.ticket_url"
            class="btn-secondary w-full"
            :href="normalizeAssetUrl(booking.ticket_url, API_BASE_URL)"
            target="_blank"
            rel="noreferrer"
          >
            Открыть билет
          </a>
        </div>
      </article>
    </div>
  </section>
</template>
