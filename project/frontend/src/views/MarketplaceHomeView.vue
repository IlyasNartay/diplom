<script setup>
import { computed, onMounted, ref } from 'vue'

import MarketplaceEventCard from '@/components/MarketplaceEventCard.vue'
import { CITY_COORDINATES, normalizeCityName } from '@/config/cities'
import { api } from '@/lib/api'
import { formatMoney, normalizeAssetUrl } from '@/lib/format'
import { useAuthStore } from '@/stores/auth'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const theme = useThemeStore()
const language = useLanguageStore()

const labelMap = {
  Concerts: { ru: 'Концерты', en: 'Concerts' },
  Festivals: { ru: 'Фестивали', en: 'Festivals' },
  Classical: { ru: 'Классика', en: 'Classical' },
  Almaty: { ru: 'Алматы', en: 'Almaty' },
  Astana: { ru: 'Астана', en: 'Astana' },
  Konaev: { ru: 'Конаев', en: 'Konaev' }
}

const events = ref([])
const categories = ref([])
const cities = ref([])
const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const selectedCategoryId = ref('')
const selectedCityId = ref('')
const selectedDay = ref('')
const quickRange = ref('all')
const geoPromptVisible = ref(false)
const geoLoading = ref(false)
const detectedCityId = ref('')
const detectedCityLabel = ref('')

const locale = computed(() => (language.isRussian.value ? 'ru-RU' : 'en-US'))
const dayFormatter = computed(() => new Intl.DateTimeFormat(locale.value, { day: 'numeric' }))
const monthFormatter = computed(() => new Intl.DateTimeFormat(locale.value, { month: 'short' }))
const weekdayFormatter = computed(() => new Intl.DateTimeFormat(locale.value, { weekday: 'short' }))
const heroDateFormatter = computed(() => new Intl.DateTimeFormat(locale.value, {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit'
}))

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      search: `Найти среди ${events.value.length || 0} событий...`,
      allCities: 'Все города',
      allEvents: 'Все события',
      allDates: 'Все даты',
      today: 'Сегодня',
      tomorrow: 'Завтра',
      weekend: 'Выходные',
      week: 'Неделя',
      reset: 'Сбросить',
      selected: 'Сейчас выбрано',
      events: 'События',
      categories: 'Категории',
      popular: 'Популярное',
      more: 'еще',
      myTickets: 'Мои билеты',
      login: 'Войти',
      noResults: 'Ничего не найдено',
      noResultsText: 'Попробуй сменить город, категорию или дату. Можно быстро вернуться ко всем событиям через кнопку сброса.',
      dateTbd: 'Дата уточняется',
      geoAsk: 'Разрешить геолокацию, чтобы подобрать ближайший город?',
      geoConfirm: 'Похоже, вы в городе',
      geoDetect: 'Определить город',
      geoUse: 'Да, выбрать',
      geoLater: 'Позже',
      geoHint: 'Мы не сохраняем координаты, только помогаем выбрать город афиши.',
      from: 'от'
    }
  }

  return {
    search: `Search across ${events.value.length || 0} events...`,
    allCities: 'All cities',
    allEvents: 'All events',
    allDates: 'All dates',
    today: 'Today',
    tomorrow: 'Tomorrow',
    weekend: 'Weekend',
    week: 'Week',
    reset: 'Reset',
    selected: 'Current filters',
    events: 'Events',
    categories: 'Categories',
    popular: 'Popular',
    more: 'more',
    myTickets: 'My tickets',
    login: 'Sign in',
    noResults: 'Nothing found',
    noResultsText: 'Try changing the city, category, or date. You can quickly return to all events with reset.',
    dateTbd: 'Date to be confirmed',
    geoAsk: 'Allow geolocation to suggest the nearest city?',
    geoConfirm: 'It looks like you are in',
    geoDetect: 'Detect city',
    geoUse: 'Use this city',
    geoLater: 'Later',
    geoHint: 'We do not store coordinates, only use them to suggest a city.',
    from: 'from'
  }
})

function toDayKey(value) {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return ''
  }

  const year = parsed.getFullYear()
  const month = `${parsed.getMonth() + 1}`.padStart(2, '0')
  const day = `${parsed.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function startOfDay(value) {
  const date = new Date(value)
  date.setHours(0, 0, 0, 0)
  return date
}

function dayDiff(target, base) {
  const distance = startOfDay(target).getTime() - startOfDay(base).getTime()
  return Math.round(distance / 86400000)
}

function nextSessionFor(event) {
  return [...(event.sessions || [])]
    .sort((left, right) => new Date(left.start_time) - new Date(right.start_time))[0] || null
}

function posterUrlFor(event) {
  return normalizeAssetUrl(event.poster_url || '', '')
}

function displayLabel(value) {
  const key = language.isRussian.value ? 'ru' : 'en'
  return labelMap[value]?.[key] || value
}

function eventSearchBlob(event) {
  return [
    event.title,
    event.description,
    event.category?.name_ru,
    event.category?.name_en,
    event.city?.name_ru,
    event.city?.name_en,
    ...(event.sessions || []).map((session) => session.hall_name)
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function sessionMatchesWindow(session) {
  const sessionDate = new Date(session.start_time)
  if (Number.isNaN(sessionDate.getTime())) {
    return false
  }

  if (selectedDay.value) {
    return toDayKey(session.start_time) === selectedDay.value
  }

  if (quickRange.value === 'all') {
    return true
  }

  const today = new Date()
  const diff = dayDiff(sessionDate, today)

  if (quickRange.value === 'today') {
    return diff === 0
  }

  if (quickRange.value === 'tomorrow') {
    return diff === 1
  }

  if (quickRange.value === 'week') {
    return diff >= 0 && diff <= 6
  }

  if (quickRange.value === 'weekend') {
    const day = sessionDate.getDay()
    return diff >= 0 && diff <= 14 && (day === 0 || day === 6)
  }

  return true
}

function distanceBetween(lat1, lon1, lat2, lon2) {
  const toRadians = (value) => (value * Math.PI) / 180
  const earthRadiusKm = 6371
  const dLat = toRadians(lat2 - lat1)
  const dLon = toRadians(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return earthRadiusKm * c
}

function findNearestCity(latitude, longitude) {
  let closest = null

  for (const city of cities.value) {
    const coords = CITY_COORDINATES[normalizeCityName(city)]
    if (!coords) {
      continue
    }

    const distance = distanceBetween(latitude, longitude, coords.lat, coords.lon)
    if (!closest || distance < closest.distance) {
      closest = { city, distance }
    }
  }

  return closest
}

function dismissGeoPrompt() {
  geoPromptVisible.value = false
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('ticketon-geo-prompted', '1')
  }
}

function applyDetectedCity() {
  if (detectedCityId.value) {
    selectedCityId.value = detectedCityId.value
  }
  dismissGeoPrompt()
}

function requestLocation() {
  if (typeof window === 'undefined' || !navigator.geolocation) {
    geoPromptVisible.value = false
    return
  }

  geoLoading.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      geoLoading.value = false
      const match = findNearestCity(position.coords.latitude, position.coords.longitude)
      if (!match?.city) {
        geoPromptVisible.value = false
        return
      }
      detectedCityId.value = match.city.id
      detectedCityLabel.value = displayLabel(match.city.name_ru)
    },
    () => {
      geoLoading.value = false
      dismissGeoPrompt()
    },
    { enableHighAccuracy: false, timeout: 7000, maximumAge: 300000 }
  )
}

const enrichedEvents = computed(() =>
  [...events.value]
    .map((event) => ({
      ...event,
      nextSession: nextSessionFor(event)
    }))
    .sort((left, right) => {
      if (!left.nextSession && !right.nextSession) {
        return left.title.localeCompare(right.title)
      }
      if (!left.nextSession) {
        return 1
      }
      if (!right.nextSession) {
        return -1
      }
      return new Date(left.nextSession.start_time) - new Date(right.nextSession.start_time)
    })
)

const categoryTabs = computed(() => [
  { id: '', label: t.value.allEvents },
  ...categories.value.map((category) => ({
    id: category.id,
    label: displayLabel(category.name_ru)
  }))
])

const cityTabs = computed(() => [
  { id: '', label: t.value.allCities },
  ...cities.value.map((city) => ({
    id: city.id,
    label: displayLabel(city.name_ru)
  }))
])

const calendarDays = computed(() => {
  const unique = new Map()

  for (const event of enrichedEvents.value) {
    for (const session of event.sessions || []) {
      const key = toDayKey(session.start_time)
      if (!key || unique.has(key)) {
        continue
      }

      const parsed = new Date(session.start_time)
      unique.set(key, {
        key,
        day: dayFormatter.value.format(parsed),
        weekday: weekdayFormatter.value.format(parsed),
        month: monthFormatter.value.format(parsed),
        date: parsed
      })
    }
  }

  return [...unique.values()].sort((left, right) => left.date - right.date).slice(0, 14)
})

const filteredEvents = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return enrichedEvents.value.filter((event) => {
    if (selectedCategoryId.value && event.category?.id !== selectedCategoryId.value) {
      return false
    }

    if (selectedCityId.value && event.city?.id !== selectedCityId.value) {
      return false
    }

    if (query && !eventSearchBlob(event).includes(query)) {
      return false
    }

    if (!event.sessions?.length) {
      return quickRange.value === 'all' && !selectedDay.value
    }

    return event.sessions.some((session) => sessionMatchesWindow(session))
  })
})

const heroEvent = computed(() => filteredEvents.value[0] || null)
const heroSideEvents = computed(() => filteredEvents.value.slice(1, 3))
const popularEvents = computed(() => filteredEvents.value.slice(0, 8))

const activeCityLabel = computed(() => {
  if (!selectedCityId.value) {
    return t.value.allCities
  }
  return displayLabel(cities.value.find((city) => city.id === selectedCityId.value)?.name_ru) || t.value.allCities
})

const activeDateLabel = computed(() => {
  if (selectedDay.value) {
    const item = calendarDays.value.find((day) => day.key === selectedDay.value)
    return item ? `${item.day} ${item.month}` : t.value.allDates
  }

  const labels = {
    all: t.value.allDates,
    today: t.value.today,
    tomorrow: t.value.tomorrow,
    weekend: t.value.weekend,
    week: t.value.week
  }

  return labels[quickRange.value] || t.value.allDates
})

async function loadHomeData() {
  loading.value = true
  error.value = ''

  try {
    const [eventPayload, categoryPayload, cityPayload] = await Promise.all([
      api.get('/api/events?limit=1000'),
      api.get('/api/categories'),
      api.get('/api/cities')
    ])

    events.value = eventPayload.events || []
    categories.value = categoryPayload
    cities.value = cityPayload
  } catch (err) {
    error.value = err.message || 'Failed to load events'
  } finally {
    loading.value = false
  }
}

function setQuickRange(range) {
  quickRange.value = range
  selectedDay.value = ''
}

function pickDay(dayKey) {
  selectedDay.value = dayKey
  quickRange.value = 'all'
}

function resetFilters() {
  searchQuery.value = ''
  selectedCategoryId.value = ''
  selectedCityId.value = ''
  selectedDay.value = ''
  quickRange.value = 'all'
}

onMounted(async () => {
  auth.hydrate()
  theme.hydrate()
  language.hydrate()
  await loadHomeData()

  if (
    typeof window !== 'undefined' &&
    !window.localStorage.getItem('ticketon-geo-prompted') &&
    !selectedCityId.value &&
    cities.value.length
  ) {
    geoPromptVisible.value = true
  }
})
</script>

<template>
  <div
    class="space-y-6 pb-6 transition-colors duration-300 sm:space-y-8 sm:pb-10"
    :class="theme.isDark.value ? 'bg-[#090b18] text-white' : 'bg-[#f6f7fb] text-slate-900'"
  >
    <section class="overflow-hidden border-b" :class="theme.isDark.value ? 'border-slate-800 bg-[#0b1022]' : 'border-slate-200 bg-white'">
      <div class="mx-auto max-w-[94rem] px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex items-center gap-3">
            <img src="/branding/logo_sdu.png" alt="SDU" class="h-14 w-auto object-contain sm:h-16" />
            <div>
              <div class="text-xl font-black uppercase tracking-[0.02em] sm:text-2xl" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">
                High-Load Ticket Booking System
              </div>
              <div class="text-xs uppercase tracking-[0.3em]" :class="theme.isDark.value ? 'text-sdu-copper/80' : 'text-emerald-700'">
                Microservices architecture
              </div>
            </div>
          </div>

          <div class="flex flex-1 items-center gap-3 lg:mx-8">
            <label class="flex w-full items-center gap-3 rounded-full border border-slate-200 bg-slate-100 px-4 py-3 text-slate-500 shadow-inner">
              <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="m20 20-3.5-3.5"></path>
              </svg>
              <input
                v-model="searchQuery"
                type="search"
                class="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400"
                :placeholder="t.search"
              />
            </label>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full border transition"
              :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-white hover:bg-white/10' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'"
              @click="theme.toggleTheme()"
            >
              <svg v-if="theme.isDark.value" viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="4"></circle>
                <path d="M12 2v2.5"></path>
                <path d="M12 19.5V22"></path>
                <path d="m4.93 4.93 1.77 1.77"></path>
                <path d="m17.3 17.3 1.77 1.77"></path>
                <path d="M2 12h2.5"></path>
                <path d="M19.5 12H22"></path>
                <path d="m4.93 19.07 1.77-1.77"></path>
                <path d="m17.3 6.7 1.77-1.77"></path>
              </svg>
              <svg v-else viewBox="0 0 24 24" class="h-5 w-5" fill="currentColor">
                <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 1 0 9.8 9.8Z"></path>
              </svg>
            </button>

            <button
              type="button"
              class="rounded-full border px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] transition"
              :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-white hover:bg-white/10' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'"
              @click="language.toggleLanguage()"
            >
              {{ language.isRussian.value ? 'EN' : 'RU' }}
            </button>

            <template v-if="auth.isAuthenticated">
              <RouterLink to="/history" class="rounded-full border border-slate-200 px-4 py-3 text-sm font-medium text-white">
                {{ t.myTickets }}
              </RouterLink>
            </template>
            <template v-else>
              <RouterLink to="/login" class="rounded-full border border-slate-200 px-4 py-3 text-sm font-medium text-white">
                {{ t.login }}
              </RouterLink>
            </template>
          </div>
        </div>
      </div>

      <div class="border-t" :class="theme.isDark.value ? 'border-slate-800 bg-[#0f172a]' : 'border-slate-200 bg-slate-50'">
        <div class="mx-auto flex max-w-[94rem] gap-2 overflow-x-auto px-4 py-3 sm:px-6 lg:px-8">
          <button
            v-for="category in categoryTabs"
            :key="category.id || 'all'"
            type="button"
            class="whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition"
            :class="
              selectedCategoryId === category.id
                ? theme.isDark.value
                  ? 'bg-sdu-copper text-sdu-night'
                  : 'bg-slate-900 text-white'
                : theme.isDark.value
                  ? 'bg-white/5 text-slate-200 ring-1 ring-white/10 hover:bg-white/10'
                  : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100'
            "
            @click="selectedCategoryId = category.id"
          >
            {{ category.label }}
          </button>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-[94rem] px-4 sm:px-6 lg:px-8">
      <div
        class="rounded-[2rem] px-4 py-6 shadow-[0_24px_70px_rgba(15,23,42,0.08)] ring-1 transition-colors duration-300 sm:px-6 sm:py-8 lg:px-8"
        :class="theme.isDark.value ? 'bg-[#0f172a] ring-white/10' : 'bg-white ring-slate-200'"
      >
        <div
          v-if="geoPromptVisible"
          class="mb-5 flex flex-col gap-3 rounded-[1.4rem] border px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
          :class="theme.isDark.value ? 'border-sdu-copper/20 bg-sdu-copper/10' : 'border-amber-200 bg-amber-50'"
        >
          <div>
            <div class="text-sm font-semibold" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">
              {{ detectedCityLabel ? `${t.geoConfirm} ${detectedCityLabel}. ${language.isRussian.value ? 'Выбрать его?' : 'Use this city?'}` : t.geoAsk }}
            </div>
            <div class="mt-1 text-xs" :class="theme.isDark.value ? 'text-slate-300' : 'text-slate-500'">
              {{ t.geoHint }}
            </div>
          </div>
          <div class="flex gap-2">
            <button v-if="!detectedCityId" type="button" class="btn-primary px-4 py-2" :disabled="geoLoading" @click="requestLocation">
              {{ geoLoading ? (language.isRussian.value ? 'Определяем...' : 'Detecting...') : t.geoDetect }}
            </button>
            <button v-else type="button" class="btn-primary px-4 py-2" @click="applyDetectedCity">
              {{ t.geoUse }}
            </button>
            <button type="button" class="btn-secondary px-4 py-2" @click="dismissGeoPrompt">
              {{ t.geoLater }}
            </button>
          </div>
        </div>

        <div class="max-[549px]:scrollbar-none max-[549px]:overflow-x-auto">
          <div class="flex gap-2 sm:gap-3 max-[549px]:min-w-max min-[550px]:flex-wrap min-[550px]:justify-center">
            <button
              v-for="city in cityTabs"
              :key="city.id || 'all-cities'"
              type="button"
              class="whitespace-nowrap rounded-full px-4 py-2.5 text-sm font-medium transition"
              :class="
                selectedCityId === city.id
                  ? theme.isDark.value
                    ? 'bg-sdu-royal text-white ring-1 ring-sdu-copper/30'
                    : 'bg-[#172554] text-white'
                  : theme.isDark.value
                    ? 'bg-white/5 text-slate-200 ring-1 ring-white/10 hover:bg-white/10'
                    : 'bg-slate-50 text-slate-700 ring-1 ring-slate-200 hover:bg-white'
              "
              @click="selectedCityId = city.id"
            >
              {{ city.label }}
            </button>
          </div>
        </div>

        <div class="mt-6 flex flex-wrap justify-center gap-2 sm:gap-3">
          <button
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-medium transition"
            :class="theme.isDark.value ? (quickRange === 'today' && !selectedDay ? 'border-sdu-copper bg-sdu-copper text-sdu-night' : 'border-white/10 bg-white/5 text-slate-200') : (quickRange === 'today' && !selectedDay ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700')"
            @click="setQuickRange('today')"
          >
            {{ t.today }}
          </button>
          <button
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-medium transition"
            :class="theme.isDark.value ? (quickRange === 'tomorrow' && !selectedDay ? 'border-sdu-copper bg-sdu-copper text-sdu-night' : 'border-white/10 bg-white/5 text-slate-200') : (quickRange === 'tomorrow' && !selectedDay ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700')"
            @click="setQuickRange('tomorrow')"
          >
            {{ t.tomorrow }}
          </button>
          <button
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-medium transition"
            :class="theme.isDark.value ? (quickRange === 'weekend' && !selectedDay ? 'border-sdu-copper bg-sdu-copper text-sdu-night' : 'border-white/10 bg-white/5 text-slate-200') : (quickRange === 'weekend' && !selectedDay ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700')"
            @click="setQuickRange('weekend')"
          >
            {{ t.weekend }}
          </button>
          <button
            type="button"
            class="rounded-full border px-4 py-2 text-sm font-medium transition"
            :class="theme.isDark.value ? (quickRange === 'week' && !selectedDay ? 'border-sdu-copper bg-sdu-copper text-sdu-night' : 'border-white/10 bg-white/5 text-slate-200') : (quickRange === 'week' && !selectedDay ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700')"
            @click="setQuickRange('week')"
          >
            {{ t.week }}
          </button>
          <button type="button" class="rounded-full border px-4 py-2 text-sm font-medium" :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-slate-200' : 'border-slate-200 bg-white text-slate-700'" @click="resetFilters">
            {{ t.reset }}
          </button>
        </div>

        <div class="mt-6 overflow-x-auto">
          <div class="flex min-w-max gap-3 pb-2">
            <button
              v-for="day in calendarDays"
              :key="day.key"
              type="button"
              class="w-[4.5rem] rounded-[1.25rem] border px-2 py-3 text-center transition sm:w-20 sm:rounded-[1.4rem] sm:px-3"
              :class="
                selectedDay === day.key
                  ? 'border-emerald-600 bg-emerald-600 text-white shadow-[0_18px_45px_rgba(5,150,105,0.22)]'
                  : theme.isDark.value
                    ? 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'
                    : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-white'
              "
              @click="pickDay(day.key)"
            >
              <div class="text-[0.66rem] uppercase tracking-[0.2em]" :class="selectedDay === day.key ? 'text-white/80' : 'text-slate-400'">
                {{ day.month }}
              </div>
              <div class="mt-2 text-2xl font-bold">{{ day.day }}</div>
              <div class="mt-1 text-xs uppercase tracking-[0.18em]" :class="selectedDay === day.key ? 'text-white/80' : theme.isDark.value ? 'text-slate-400' : 'text-slate-500'">
                {{ day.weekday }}
              </div>
            </button>
          </div>
        </div>

        <div class="mt-6 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <RouterLink
            v-if="heroEvent"
            :to="`/events/${heroEvent.id}`"
            class="relative overflow-hidden rounded-[1.8rem] bg-slate-900 p-4 text-white shadow-[0_32px_90px_rgba(15,23,42,0.22)] sm:p-6"
          >
            <div
              class="absolute inset-0 bg-cover bg-center opacity-70"
              :style="{ backgroundImage: `linear-gradient(120deg, rgba(15,23,42,0.82), rgba(15,23,42,0.38)), url('${posterUrlFor(heroEvent)}')` }"
            ></div>
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(241,168,109,0.35),transparent_38%)]"></div>
            <div class="relative flex min-h-[16rem] flex-col justify-end sm:min-h-[22rem]">
              <div class="inline-flex w-fit rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-amber-100">
                {{ displayLabel(heroEvent.category?.name_ru) }}
              </div>
              <h2 class="mt-3 max-w-2xl font-display text-2xl leading-tight sm:mt-4 sm:text-5xl">{{ heroEvent.title }}</h2>
              <p class="mt-3 max-w-2xl text-sm leading-6 text-white/80 sm:mt-4 sm:text-base sm:leading-7">
                {{ heroEvent.description }}
              </p>
              <div class="mt-4 flex flex-wrap items-center gap-3 text-xs text-white/90 sm:mt-6 sm:gap-4 sm:text-sm">
                <span>{{ heroEvent.nextSession ? heroDateFormatter.format(new Date(heroEvent.nextSession.start_time)) : t.dateTbd }}</span>
                <span>{{ heroEvent.nextSession?.hall_name }}</span>
                <span>{{ displayLabel(heroEvent.city?.name_ru) }}</span>
                <span>{{ heroEvent.nextSession ? `${t.from} ${formatMoney(heroEvent.nextSession.price)}` : '' }}</span>
              </div>
            </div>
          </RouterLink>

          <div class="grid gap-4">
            <RouterLink
              v-for="event in heroSideEvents"
              :key="event.id"
              :to="`/events/${event.id}`"
              class="flex overflow-hidden rounded-[1.45rem] border transition"
              :class="theme.isDark.value ? 'border-white/10 bg-white/5 hover:bg-white/10' : 'border-slate-200 bg-slate-50 hover:bg-white'"
            >
              <img :src="posterUrlFor(event)" :alt="event.title" class="h-full w-24 shrink-0 object-cover sm:w-40" />
              <div class="flex flex-1 flex-col justify-between p-3 sm:p-4">
                <div>
                  <div class="text-xs uppercase tracking-[0.24em]" :class="theme.isDark.value ? 'text-sdu-copper/80' : 'text-emerald-700'">{{ displayLabel(event.category?.name_ru) }}</div>
                  <div class="mt-2 line-clamp-2 text-base font-semibold sm:text-xl" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ event.title }}</div>
                </div>
                <div class="mt-3 text-xs sm:mt-4 sm:text-sm" :class="theme.isDark.value ? 'text-slate-300' : 'text-slate-500'">
                  {{ event.nextSession ? heroDateFormatter.format(new Date(event.nextSession.start_time)) : t.dateTbd }}
                </div>
              </div>
            </RouterLink>

            <div class="rounded-[1.6rem] border p-5" :class="theme.isDark.value ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-slate-50'">
              <div class="text-xs uppercase tracking-[0.24em] text-slate-400">{{ t.selected }}</div>
              <div class="mt-3 text-2xl font-semibold" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ activeCityLabel }}</div>
              <div class="mt-2 text-sm" :class="theme.isDark.value ? 'text-slate-300' : 'text-slate-500'">{{ activeDateLabel }}</div>
              <div class="mt-6 grid grid-cols-2 gap-3">
                <div class="rounded-[1.1rem] p-4" :class="theme.isDark.value ? 'bg-sdu-night/70' : 'bg-white'">
                  <div class="text-xs uppercase tracking-[0.2em] text-slate-400">{{ t.events }}</div>
                  <div class="mt-2 text-2xl font-bold" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ filteredEvents.length }}</div>
                </div>
                <div class="rounded-[1.1rem] p-4" :class="theme.isDark.value ? 'bg-sdu-night/70' : 'bg-white'">
                  <div class="text-xs uppercase tracking-[0.2em] text-slate-400">{{ t.categories }}</div>
                  <div class="mt-2 text-2xl font-bold" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ categories.length }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="catalog" class="mx-auto max-w-[94rem] px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-4">
        <div class="h-px flex-1" :class="theme.isDark.value ? 'bg-white/10' : 'bg-slate-300'"></div>
        <div class="text-2xl font-black uppercase tracking-[0.08em] sm:text-4xl" :class="theme.isDark.value ? 'text-white' : 'text-slate-950'">{{ t.popular }}</div>
        <div class="rounded-full border px-4 py-1 text-sm font-medium" :class="theme.isDark.value ? 'border-white/10 bg-white/5 text-slate-200' : 'border-slate-300 bg-white text-slate-600'">
          {{ t.more }} {{ Math.max(filteredEvents.length - popularEvents.length, 0) }}
        </div>
        <div class="h-px flex-1" :class="theme.isDark.value ? 'bg-white/10' : 'bg-slate-300'"></div>
      </div>

      <div class="mt-6">
        <div v-if="error" class="rounded-[1.6rem] border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">
          {{ error }}
        </div>

        <div v-else-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="index in 8"
            :key="index"
            class="h-[27rem] rounded-[1.8rem] bg-[linear-gradient(90deg,#f1f5f9,#ffffff,#f1f5f9)] bg-[length:200%_100%] animate-shimmer ring-1 ring-slate-200"
          ></div>
        </div>

        <div v-else-if="!popularEvents.length" class="rounded-[1.8rem] border p-8 text-center shadow-[0_20px_50px_rgba(15,23,42,0.06)]" :class="theme.isDark.value ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white'">
          <div class="text-3xl font-display" :class="theme.isDark.value ? 'text-white' : 'text-slate-900'">{{ t.noResults }}</div>
          <p class="mt-3 text-sm" :class="theme.isDark.value ? 'text-slate-300' : 'text-slate-500'">
            {{ t.noResultsText }}
          </p>
        </div>

        <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MarketplaceEventCard v-for="event in popularEvents" :key="event.id" :event="event" />
        </div>
      </div>
    </section>
  </div>
</template>
