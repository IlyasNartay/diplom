<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SeatGrid from '@/components/SeatGrid.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { API_BASE_URL, api } from '@/lib/api'
import { formatDateTime, formatMoney, normalizeAssetUrl } from '@/lib/format'
import { useAuthStore } from '@/stores/auth'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const language = useLanguageStore()
const theme = useThemeStore()

const locale = computed(() => (language.isRussian.value ? 'ru-RU' : 'en-US'))
const route = useRoute()
const router = useRouter()

const event = ref(null)
const seats = ref([])
const selectedSessionId = ref('')
const selectedSeatIds = ref([])
const loading = ref(true)
const seatLoading = ref(false)
const bookingLoading = ref(false)
const error = ref('')
const bookingStatus = ref(null)

const activeSession = computed(() =>
  event.value?.sessions?.find((item) => item.id === selectedSessionId.value) || null
)

const selectedSeats = computed(() =>
  seats.value.filter((seat) => selectedSeatIds.value.includes(seat.id))
)

const totalPrice = computed(() =>
  selectedSeats.value.reduce((sum, seat) => sum + Number(seat.price || 0), 0)
)

const posterUrl = computed(() => normalizeAssetUrl(event.value?.poster_url || '', API_BASE_URL))

const pageClass = computed(() =>
  theme.isDark.value ? 'space-y-6 sm:space-y-8 text-white' : 'space-y-6 sm:space-y-8 text-slate-900'
)

const heroPanelClass = computed(() =>
  theme.isDark.value
    ? 'overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-glow backdrop-blur-xl'
    : 'overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]'
)

const detailPanelClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-glow backdrop-blur-xl sm:p-8 lg:p-10'
    : 'rounded-[2rem] border border-slate-200 bg-white p-5 shadow-[0_28px_90px_rgba(15,23,42,0.08)] sm:p-8 lg:p-10'
)

const sectionPanelClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[2rem] border border-white/10 bg-white/5 p-4 shadow-glow backdrop-blur-xl sm:p-6 lg:p-8'
    : 'rounded-[2rem] border border-slate-200 bg-white p-4 shadow-[0_28px_90px_rgba(15,23,42,0.08)] sm:p-6 lg:p-8'
)

const softPanelClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[1.5rem] border border-white/10 bg-sdu-ink/70 p-4 shadow-copper backdrop-blur-xl'
    : 'rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4 shadow-sm'
)

const fieldClass = computed(() =>
  theme.isDark.value
    ? 'field'
    : 'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:border-sdu-copper/70 focus:bg-white'
)

const mutedTextClass = computed(() => (theme.isDark.value ? 'text-sdu-mist/75' : 'text-slate-600'))
const subTextClass = computed(() => (theme.isDark.value ? 'text-sdu-mist/65' : 'text-slate-500'))
const labelClass = computed(() => (theme.isDark.value ? 'text-sdu-copper/75' : 'text-sdu-royal'))
const seatLegendClass = computed(() => (theme.isDark.value ? 'text-sdu-mist/70' : 'text-slate-600'))
const selectedChipClass = computed(() =>
  theme.isDark.value
    ? 'rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-white'
    : 'rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700'
)
const bottomCheckoutClass = computed(() =>
  theme.isDark.value
    ? 'fixed inset-x-4 bottom-[5.9rem] z-40 rounded-[1.35rem] border border-white/10 bg-sdu-ink/95 p-4 shadow-glow backdrop-blur-2xl md:hidden'
    : 'fixed inset-x-4 bottom-[5.9rem] z-40 rounded-[1.35rem] border border-slate-200 bg-white/95 p-4 shadow-[0_22px_70px_rgba(15,23,42,0.16)] backdrop-blur-2xl md:hidden'
)

async function loadEvent() {
  loading.value = true
  error.value = ''

  try {
    const payload = await api.get(`/api/events/${route.params.id}`)
    event.value = payload
    selectedSessionId.value = payload.sessions?.[0]?.id || ''
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить мероприятие'
  } finally {
    loading.value = false
  }
}

async function loadSeats() {
  if (!selectedSessionId.value) {
    seats.value = []
    return
  }

  seatLoading.value = true
  selectedSeatIds.value = []

  try {
    seats.value = await api.get(`/api/seats/${selectedSessionId.value}`)
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить места'
  } finally {
    seatLoading.value = false
  }
}

async function pollBookingStatus(bookingId) {
  for (let attempt = 0; attempt < 18; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 2000))
    const payload = await api.get(`/api/status/${bookingId}`)
    bookingStatus.value = payload

    if (['completed', 'payment_failed', 'seat_reservation_failed'].includes(payload.status)) {
      await loadSeats()
      return payload
    }
  }

  return bookingStatus.value
}

async function bookSeats() {
  if (!auth.isAuthenticated) {
    router.push({
      name: 'login',
      query: { redirect: route.fullPath }
    })
    return
  }

  if (!selectedSeatIds.value.length) {
    error.value = 'Сначала выбери хотя бы одно свободное место'
    return
  }

  bookingLoading.value = true
  error.value = ''
  bookingStatus.value = null

  try {
    const started = await api.post('/api/buy', {
      seat_ids: selectedSeatIds.value
    })
    bookingStatus.value = {
      booking_id: started.booking_id,
      status: 'started'
    }
    await pollBookingStatus(started.booking_id)
  } catch (err) {
    error.value = err.message || 'Не удалось оформить покупку'
  } finally {
    bookingLoading.value = false
  }
}

watch(selectedSessionId, () => {
  if (selectedSessionId.value) {
    loadSeats()
  }
})

onMounted(async () => {
  auth.hydrate()
  theme.hydrate()
  language.hydrate()
  await loadEvent()
})
</script>

<template>
  <div v-if="loading" :class="pageClass">
    <div
      :class="
        theme.isDark.value
          ? 'h-[28rem] rounded-[2rem] border border-white/10 bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%] animate-shimmer'
          : 'h-[28rem] rounded-[2rem] border border-slate-200 bg-[linear-gradient(90deg,rgba(255,255,255,0.65),rgba(241,245,249,1),rgba(255,255,255,0.65))] bg-[length:200%_100%] animate-shimmer'
      "
    ></div>
  </div>

  <div v-else-if="error && !event" :class="[sectionPanelClass, theme.isDark.value ? 'text-rose-200' : 'text-rose-700']">
    {{ error }}
  </div>

  <div v-else-if="event" :class="pageClass">
    <section class="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:gap-8">
      <div :class="heroPanelClass">
        <img
          v-if="posterUrl"
          :src="posterUrl"
          :alt="event.title"
          class="h-full max-h-[16rem] w-full object-cover sm:max-h-[24rem] lg:max-h-[34rem]"
        />
        <div
          v-else
          :class="
            theme.isDark.value
              ? 'flex min-h-[16rem] items-end bg-[linear-gradient(160deg,rgba(44,50,121,0.95),rgba(9,11,24,1))] p-5 sm:min-h-[22rem] sm:p-8'
              : 'flex min-h-[16rem] items-end bg-[linear-gradient(160deg,rgba(30,41,59,0.98),rgba(15,23,42,1))] p-5 sm:min-h-[22rem] sm:p-8'
          "
        >
          <div class="font-display text-4xl text-white sm:text-5xl">{{ event.title }}</div>
        </div>
      </div>

      <div :class="detailPanelClass">
        <div class="eyebrow">{{ event.category?.name_en || event.category?.name_ru || 'Event' }}</div>
        <h1 :class="theme.isDark.value ? 'mt-4 font-display text-3xl text-white sm:text-5xl' : 'mt-4 font-display text-3xl text-slate-900 sm:text-5xl'">
          {{ event.title }}
        </h1>
        <p :class="['mt-4 text-sm leading-7 sm:mt-6 sm:text-base sm:leading-8', mutedTextClass]">
          {{
            event.description ||
            'Описание мероприятия пока не добавлено, но страница уже готова к покупке и выбору мест.'
          }}
        </p>

        <div class="mt-5 grid gap-3 sm:mt-7 sm:grid-cols-2 sm:gap-4">
          <div :class="softPanelClass">
            <div class="text-xs uppercase tracking-[0.22em]" :class="labelClass">Город</div>
            <div :class="theme.isDark.value ? 'mt-2 text-base text-white sm:text-lg' : 'mt-2 text-base text-slate-900 sm:text-lg'">
              {{ event.city?.name_ru || event.city?.name_en || '—' }}
            </div>
          </div>
          <div :class="softPanelClass">
            <div class="text-xs uppercase tracking-[0.22em]" :class="labelClass">Сеансов</div>
            <div :class="theme.isDark.value ? 'mt-2 text-base text-white sm:text-lg' : 'mt-2 text-base text-slate-900 sm:text-lg'">
              {{ event.sessions?.length || 0 }}
            </div>
          </div>
        </div>

        <div class="mt-6 sm:mt-8">
          <label
            class="mb-2 block text-xs uppercase tracking-[0.24em]"
            :class="theme.isDark.value ? 'text-sdu-mist/65' : 'text-slate-500'"
          >
            Выбери сеанс
          </label>
          <select v-model="selectedSessionId" :class="fieldClass">
            <option v-for="session in event.sessions" :key="session.id" :value="session.id">
              {{ formatDateTime(session.start_time, locale) }} · {{ session.hall_name }} · {{ formatMoney(session.price) }}
            </option>
          </select>
        </div>

        <div
          v-if="activeSession"
          :class="
            theme.isDark.value
              ? 'mt-5 rounded-[1.4rem] border border-sdu-copper/20 bg-sdu-copper/10 p-4 sm:mt-6 sm:rounded-[1.75rem] sm:p-5'
              : 'mt-5 rounded-[1.4rem] border border-amber-200 bg-amber-50 p-4 sm:mt-6 sm:rounded-[1.75rem] sm:p-5'
          "
        >
          <div class="text-xs uppercase tracking-[0.24em]" :class="theme.isDark.value ? 'text-sdu-copper/80' : 'text-sdu-royal'">
            Активный сеанс
          </div>
          <div :class="theme.isDark.value ? 'mt-2 font-display text-xl text-white sm:text-2xl' : 'mt-2 font-display text-xl text-slate-900 sm:text-2xl'">
            {{ activeSession.hall_name }}
          </div>
          <div :class="['mt-1 text-sm', mutedTextClass]">{{ formatDateTime(activeSession.start_time, locale) }}</div>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[1.2fr_0.8fr] xl:gap-8">
      <div :class="sectionPanelClass">
        <div class="mb-4 flex flex-col gap-3 sm:mb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div class="eyebrow">Seat Selection</div>
            <h2 :class="theme.isDark.value ? 'mt-2 font-display text-2xl text-white sm:text-4xl' : 'mt-2 font-display text-2xl text-slate-900 sm:text-4xl'">
              Выбор мест
            </h2>
          </div>
          <div :class="['flex flex-wrap gap-x-2 gap-y-2 text-[0.68rem] sm:text-sm', seatLegendClass]">
            <span class="inline-flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-emerald-400/70"></span>Свободно</span>
            <span class="inline-flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-sdu-copper"></span>Выбрано</span>
            <span class="inline-flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-amber-400/80"></span>Reserved</span>
            <span class="inline-flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-rose-500/80"></span>Sold</span>
          </div>
        </div>

        <div v-if="seatLoading" :class="[softPanelClass, mutedTextClass]">
          Загружаю карту мест...
        </div>
        <div v-else-if="!seats.length" :class="[softPanelClass, mutedTextClass]">
          Для этого сеанса места пока не созданы.
        </div>
        <SeatGrid v-else v-model="selectedSeatIds" :seats="seats" />
      </div>

      <aside class="space-y-4 sm:space-y-6">
        <div :class="sectionPanelClass">
          <div class="eyebrow">Checkout</div>
          <h3 :class="theme.isDark.value ? 'mt-2 font-display text-2xl text-white sm:text-3xl' : 'mt-2 font-display text-2xl text-slate-900 sm:text-3xl'">
            Подтверждение
          </h3>

          <div class="mt-5 space-y-3">
            <div :class="['flex items-center justify-between text-sm', mutedTextClass]">
              <span>Выбрано мест</span>
              <span :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ selectedSeatIds.length }}</span>
            </div>
            <div :class="['flex items-center justify-between text-sm', mutedTextClass]">
              <span>Сумма</span>
              <span :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ formatMoney(totalPrice) }}</span>
            </div>
          </div>

          <div
            v-if="selectedSeats.length"
            :class="theme.isDark.value ? 'mt-5 rounded-[1.5rem] border border-white/10 bg-white/5 p-4' : 'mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4'"
          >
            <div class="text-xs uppercase tracking-[0.22em]" :class="labelClass">Места</div>
            <div class="mt-3 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
              <span
                v-for="seat in selectedSeats"
                :key="seat.id"
                :class="selectedChipClass"
              >
                Ряд {{ seat.row }}, место {{ seat.number }}
              </span>
            </div>
          </div>

          <p :class="['mt-5 text-sm leading-7', mutedTextClass]">
            После нажатия запускается backend saga: резерв мест, создание заказа, оплата и выпуск билета.
          </p>

          <button class="btn-primary mt-5 w-full" :disabled="bookingLoading" @click="bookSeats">
            {{ bookingLoading ? 'Обрабатываем покупку...' : 'Купить билет' }}
          </button>

          <p v-if="!auth.isAuthenticated" :class="['mt-3 text-xs leading-6', subTextClass]">
            Для покупки потребуется вход. Если ты не авторизован, кнопка переведет на экран логина.
          </p>
        </div>

        <div
          v-if="error"
          :class="theme.isDark.value ? 'panel p-5 text-sm text-rose-200' : 'rounded-[2rem] border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700'"
        >
          {{ error }}
        </div>

        <div v-if="bookingStatus" :class="sectionPanelClass">
          <div class="flex items-center justify-between gap-4">
            <div>
              <div class="text-xs uppercase tracking-[0.22em]" :class="labelClass">Статус бронирования</div>
              <div :class="theme.isDark.value ? 'mt-2 font-display text-xl text-white sm:text-2xl' : 'mt-2 font-display text-xl text-slate-900 sm:text-2xl'">
                Booking #{{ bookingStatus.booking_id }}
              </div>
            </div>
            <StatusBadge :status="bookingStatus.status" />
          </div>

          <p v-if="bookingStatus.error_reason" :class="['mt-4 text-sm', theme.isDark.value ? 'text-rose-200' : 'text-rose-700']">
            {{ bookingStatus.error_reason }}
          </p>

          <a
            v-if="bookingStatus.ticket_url"
            class="btn-secondary mt-5 w-full"
            :href="normalizeAssetUrl(bookingStatus.ticket_url, API_BASE_URL)"
            target="_blank"
            rel="noreferrer"
          >
            Открыть билет
          </a>
        </div>
      </aside>
    </section>

    <div v-if="selectedSeatIds.length || bookingLoading" :class="bottomCheckoutClass">
      <div class="flex items-center justify-between gap-4">
        <div>
          <div class="text-[0.68rem] uppercase tracking-[0.2em]" :class="labelClass">Mobile checkout</div>
          <div :class="['mt-1 text-sm', theme.isDark.value ? 'text-white' : 'text-slate-900']">
            {{ selectedSeatIds.length }} seats · {{ formatMoney(totalPrice) }}
          </div>
        </div>
        <button class="btn-primary min-w-[8.5rem] px-4 py-3" :disabled="bookingLoading" @click="bookSeats">
          {{ bookingLoading ? 'Processing...' : 'Buy now' }}
        </button>
      </div>
    </div>
  </div>
</template>
