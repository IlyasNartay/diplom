<script setup>
import { computed, onMounted, ref } from 'vue'

import StatusBadge from '@/components/StatusBadge.vue'
import { API_BASE_URL, api } from '@/lib/api'
import { formatDateTime, normalizeAssetUrl, resolveTicketUrl } from '@/lib/format'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const language = useLanguageStore()
const theme = useThemeStore()

const isDark = computed(() => theme.isDark)

const history = ref([])
const loading = ref(true)
const error = ref('')

const locale = computed(() => (language.isRussian.value ? 'ru-RU' : 'en-US'))

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      eyebrow: 'Архив бронирований',
      title: 'История бронирований',
      intro:
        'Здесь отображаются записи из orchestrator: итоговый статус, ссылка на билет и то, прошёл ли сеанс.',
      loadError: 'Не удалось получить историю бронирований',
      emptyTitle: 'Пока пусто',
      emptyText: 'После первой покупки здесь появятся статусы и ссылки на билеты.',
      untitled: 'Мероприятие без названия',
      bookingId: 'ID бронирования',
      eventState: 'Состояние события',
      active: 'Активно',
      sessionPassed: 'Сеанс прошёл',
      yes: 'Да',
      no: 'Нет',
      openTicket: 'Скачать билет'
    }
  }

  return {
    eyebrow: 'Booking archive',
    title: 'Your bookings',
    intro:
      'Records from the orchestrator: final status, ticket link, and whether the session has already passed.',
    loadError: 'Could not load booking history',
    emptyTitle: 'Nothing here yet',
    emptyText: 'After your first purchase, statuses and ticket links will show up here.',
    untitled: 'Untitled event',
    bookingId: 'Booking ID',
    eventState: 'Event status',
    active: 'Active',
    sessionPassed: 'Session passed',
    yes: 'Yes',
    no: 'No',
    openTicket: 'Download ticket'
  }
})

const pageClass = computed(() =>
  theme.isDark ? 'space-y-6 text-white' : 'space-y-6 text-slate-900'
)

const eyebrowClass = computed(() =>
  theme.isDark ? 'eyebrow' : 'text-xs uppercase tracking-[0.34em] text-emerald-700'
)

const introClass = computed(() =>
  theme.isDark ? 'mt-4 max-w-2xl text-sm leading-7 text-sdu-mist/75' : 'mt-4 max-w-2xl text-sm leading-7 text-slate-600'
)

const titleClass = computed(() =>
  theme.isDark
    ? 'mt-3 font-display text-3xl text-white sm:text-4xl'
    : 'mt-3 font-display text-3xl text-slate-900 sm:text-4xl'
)

const panelClass = computed(() =>
  theme.isDark
    ? 'panel'
    : 'rounded-[2rem] border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]'
)

const errorPanelClass = computed(() =>
  theme.isDark ? 'panel p-5 text-sm text-rose-200' : 'rounded-[2rem] border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800'
)

const shimmerClass = computed(() =>
  theme.isDark
    ? 'panel h-40 animate-shimmer bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%]'
    : 'h-40 rounded-[2rem] border border-slate-200 bg-[linear-gradient(90deg,rgba(241,245,249,1),rgba(255,255,255,1),rgba(241,245,249,1))] bg-[length:200%_100%] animate-shimmer'
)

const articleTitleClass = computed(() =>
  theme.isDark
    ? 'mt-4 font-display text-2xl text-white sm:text-3xl'
    : 'mt-4 font-display text-2xl text-slate-900 sm:text-3xl'
)

const metaClass = computed(() =>
  theme.isDark ? 'mt-3 break-all text-sm leading-7 text-sdu-mist/75' : 'mt-3 break-all text-sm leading-7 text-slate-600'
)

const seatChipClass = computed(() =>
  theme.isDark
    ? 'rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-sdu-mist/80'
    : 'rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600'
)

const sideCardClass = computed(() =>
  theme.isDark
    ? 'flex flex-col justify-between gap-4 rounded-[1.35rem] border border-white/10 bg-white/5 p-4 sm:rounded-[1.6rem] sm:p-5'
    : 'flex flex-col justify-between gap-4 rounded-[1.35rem] border border-slate-200 bg-slate-50 p-4 sm:rounded-[1.6rem] sm:p-5'
)

const sideHeadingClass = computed(() =>
  theme.isDark ? 'text-xs uppercase tracking-[0.22em] text-sdu-copper/75' : 'text-xs uppercase tracking-[0.22em] text-sdu-royal'
)

const sideBodyClass = computed(() =>
  theme.isDark ? 'mt-3 space-y-2 text-sm text-sdu-mist/75' : 'mt-3 space-y-2 text-sm text-slate-600'
)

const dateMetaClass = computed(() =>
  theme.isDark ? 'text-xs uppercase tracking-[0.2em] text-sdu-mist/60' : 'text-xs uppercase tracking-[0.2em] text-slate-500'
)

function ticketHref(booking) {
  return normalizeAssetUrl(resolveTicketUrl(booking), API_BASE_URL)
}

function canDownloadTicket(booking) {
  return Boolean(resolveTicketUrl(booking))
}

async function loadHistory() {
  loading.value = true
  error.value = ''

  try {
    history.value = await api.get('/api/history/me')
  } catch (err) {
    error.value = err.message || t.value.loadError
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  language.hydrate()
  theme.hydrate()
  loadHistory()
})
</script>

<template>
  <section :class="pageClass">
    <div class="mb-5 sm:mb-6">
      <div :class="eyebrowClass">{{ t.eyebrow }}</div>
      <h1 :class="titleClass">{{ t.title }}</h1>
      <p :class="introClass">
        {{ t.intro }}
      </p>
    </div>

    <div v-if="error" :class="errorPanelClass">
      {{ error }}
    </div>

    <div v-else-if="loading" class="space-y-4">
      <div
        v-for="index in 3"
        :key="index"
        :class="shimmerClass"
      ></div>
    </div>

    <div v-else-if="!history.length" :class="[panelClass, 'p-6 text-center sm:p-8']">
      <div :class="isDark ? 'font-display text-3xl text-white' : 'font-display text-3xl text-slate-900'">
        {{ t.emptyTitle }}
      </div>
      <p :class="[introClass, 'mt-3 text-center']">
        {{ t.emptyText }}
      </p>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="booking in history"
        :key="booking.booking_id"
        :class="[panelClass, 'grid gap-4 p-5 sm:gap-6 sm:p-8 lg:grid-cols-[1.4fr_0.6fr]']"
      >
        <div>
          <div class="flex flex-wrap items-center gap-3">
            <StatusBadge :status="booking.status" />
            <span :class="dateMetaClass">
              {{ formatDateTime(booking.created_at, locale) }}
            </span>
          </div>

          <h2 :class="articleTitleClass">
            {{ booking.event_title || t.untitled }}
          </h2>

          <p :class="metaClass">
            {{ t.bookingId }}: {{ booking.booking_id }}
          </p>

          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="seatId in booking.seat_ids"
              :key="seatId"
              :class="seatChipClass"
            >
              {{ seatId }}
            </span>
          </div>

          <p v-if="booking.error_reason" :class="isDark ? 'mt-4 text-sm text-rose-200' : 'mt-4 text-sm text-rose-700'">
            {{ booking.error_reason }}
          </p>

          <a
            v-if="canDownloadTicket(booking)"
            class="btn-primary mt-5 inline-flex w-full sm:w-auto"
            :href="ticketHref(booking)"
            target="_blank"
            rel="noopener noreferrer"
            :download="`${booking.booking_id}.pdf`"
          >
            {{ t.openTicket }}
          </a>
        </div>

        <div :class="sideCardClass">
          <div :class="sideHeadingClass">{{ t.eventState }}</div>
          <div :class="sideBodyClass">
            <div>{{ t.active }}: {{ booking.event_is_active ? t.yes : t.no }}</div>
            <div>{{ t.sessionPassed }}: {{ booking.session_has_passed ? t.yes : t.no }}</div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
