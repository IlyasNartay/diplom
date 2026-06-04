<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { api } from '@/lib/api'
import { formatDateTime, formatMoney } from '@/lib/format'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

const categories = ref([])
const cities = ref([])
const events = ref([])
const loading = ref(true)
const message = ref('')
const error = ref('')

const selectedEventId = ref('')
const eventSearch = ref('')
const eventCategoryFilter = ref('')
const eventCityFilter = ref('')
const createPosterFile = ref(null)
const replacePosterFile = ref(null)
const createPosterPreviewUrl = ref('')
const replacePosterPreviewUrl = ref('')

const categoryForm = reactive({
  name_ru: '',
  name_en: '',
  name_kz: ''
})

const cityForm = reactive({
  name_ru: '',
  name_en: '',
  name_kz: ''
})

const eventForm = reactive({
  title: '',
  description: '',
  video_url: '',
  category_id: '',
  city_id: ''
})

const eventEdit = reactive({
  title: '',
  description: '',
  video_url: '',
  category_id: '',
  city_id: ''
})

const sessionForm = reactive({
  start_time: '',
  hall_name: '',
  price: ''
})

const seatsForm = reactive({
  session_id: '',
  rows: 5,
  seats_per_row: 8
})

const categoryDrafts = reactive({})
const cityDrafts = reactive({})
const sessionDrafts = reactive({})

const panelClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[2rem] border border-white/10 bg-white/5 shadow-glow backdrop-blur-xl'
    : 'rounded-[2rem] border border-slate-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.08)]'
)

const panelSoftClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[1.5rem] border border-white/10 bg-sdu-ink/70 shadow-copper'
    : 'rounded-[1.5rem] border border-slate-200 bg-slate-50 shadow-sm'
)

const textMutedClass = computed(() => (theme.isDark.value ? 'text-sdu-mist/75' : 'text-slate-600'))
const headingClass = computed(() => (theme.isDark.value ? 'text-white' : 'text-slate-900'))
const metricCardClass = computed(() =>
  theme.isDark.value
    ? 'rounded-[1.3rem] border border-white/10 bg-white/5 p-4'
    : 'rounded-[1.3rem] border border-slate-200 bg-white p-4'
)
const chipButtonClass = computed(() =>
  theme.isDark.value
    ? 'rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-sdu-mist/80 transition hover:bg-white/10'
    : 'rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 transition hover:bg-slate-100'
)

const selectedEvent = computed(() =>
  events.value.find((item) => item.id === selectedEventId.value) || null
)

const filteredEvents = computed(() => {
  const query = eventSearch.value.trim().toLowerCase()

  return events.value.filter((event) => {
    const matchesQuery =
      !query ||
      event.title.toLowerCase().includes(query) ||
      event.city?.name_ru?.toLowerCase().includes(query) ||
      event.category?.name_ru?.toLowerCase().includes(query)

    const matchesCategory = !eventCategoryFilter.value || event.category?.id === eventCategoryFilter.value
    const matchesCity = !eventCityFilter.value || event.city?.id === eventCityFilter.value

    return matchesQuery && matchesCategory && matchesCity
  })
})

const selectedEventSessions = computed(() =>
  [...(selectedEvent.value?.sessions || [])].sort(
    (left, right) => new Date(left.start_time) - new Date(right.start_time)
  )
)

const totalSessions = computed(() =>
  events.value.reduce((count, event) => count + (event.sessions?.length || 0), 0)
)

const upcomingSessions = computed(() => {
  const now = Date.now()
  return events.value.reduce((count, event) => {
    const upcoming = (event.sessions || []).filter((session) => new Date(session.start_time).getTime() >= now)
    return count + upcoming.length
  }, 0)
})

const selectedEventPoster = computed(
  () => replacePosterPreviewUrl.value || selectedEvent.value?.poster_url || ''
)

function resetDraftCollection(collection) {
  for (const key of Object.keys(collection)) {
    delete collection[key]
  }
}

function revokePreviewUrl(url) {
  if (url) {
    URL.revokeObjectURL(url)
  }
}

function setPreviewUrl(target, file) {
  revokePreviewUrl(target.value)
  target.value = file ? URL.createObjectURL(file) : ''
}

function toDateTimeLocalValue(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const timezoneOffsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 16)
}

function toIsoDateTime(value) {
  if (!value) {
    return null
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return date.toISOString()
}

function rebuildDrafts() {
  resetDraftCollection(categoryDrafts)
  resetDraftCollection(cityDrafts)
  resetDraftCollection(sessionDrafts)

  for (const category of categories.value) {
    categoryDrafts[category.id] = {
      name_ru: category.name_ru,
      name_en: category.name_en,
      name_kz: category.name_kz
    }
  }

  for (const city of cities.value) {
    cityDrafts[city.id] = {
      name_ru: city.name_ru,
      name_en: city.name_en,
      name_kz: city.name_kz
    }
  }

  for (const event of events.value) {
    for (const session of event.sessions || []) {
      sessionDrafts[session.id] = {
        start_time: toDateTimeLocalValue(session.start_time),
        hall_name: session.hall_name,
        price: session.price
      }
    }
  }
}

function syncSelectedEvent() {
  const event = selectedEvent.value
  if (!event) {
    eventEdit.title = ''
    eventEdit.description = ''
    eventEdit.video_url = ''
    eventEdit.category_id = ''
    eventEdit.city_id = ''
    seatsForm.session_id = ''
    return
  }

  eventEdit.title = event.title || ''
  eventEdit.description = event.description || ''
  eventEdit.video_url = event.video_url || ''
  eventEdit.category_id = event.category?.id || ''
  eventEdit.city_id = event.city?.id || ''

  const firstSessionId = event.sessions?.[0]?.id || ''
  if (!selectedEventSessions.value.some((session) => session.id === seatsForm.session_id)) {
    seatsForm.session_id = firstSessionId
  }
}

async function loadReferenceData() {
  loading.value = true
  error.value = ''

  try {
    const [categoryPayload, cityPayload, eventPayload] = await Promise.all([
      api.get('/api/categories'),
      api.get('/api/cities'),
      api.get('/api/events?limit=1000')
    ])

    categories.value = categoryPayload
    cities.value = cityPayload
    events.value = eventPayload.events || []

    if (!eventForm.category_id) {
      eventForm.category_id = categories.value[0]?.id || ''
    }
    if (!eventForm.city_id) {
      eventForm.city_id = cities.value[0]?.id || ''
    }
    if (!selectedEventId.value || !events.value.some((event) => event.id === selectedEventId.value)) {
      selectedEventId.value = filteredEvents.value[0]?.id || events.value[0]?.id || ''
    }

    rebuildDrafts()
    syncSelectedEvent()
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить административные данные'
  } finally {
    loading.value = false
  }
}

function resetMessage() {
  message.value = ''
  error.value = ''
}

function resetCreateEventForm() {
  eventForm.title = ''
  eventForm.description = ''
  eventForm.video_url = ''
  createPosterFile.value = null
  setPreviewUrl(createPosterPreviewUrl, null)
}

function onCreatePosterChange(event) {
  createPosterFile.value = event.target.files?.[0] || null
  setPreviewUrl(createPosterPreviewUrl, createPosterFile.value)
}

function onReplacePosterChange(event) {
  replacePosterFile.value = event.target.files?.[0] || null
  setPreviewUrl(replacePosterPreviewUrl, replacePosterFile.value)
}

function resetEventFilters() {
  eventSearch.value = ''
  eventCategoryFilter.value = ''
  eventCityFilter.value = ''
}

async function createCategory() {
  resetMessage()
  try {
    await api.post('/api/admin/categories', categoryForm)
    message.value = 'Категория создана'
    categoryForm.name_ru = ''
    categoryForm.name_en = ''
    categoryForm.name_kz = ''
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось создать категорию'
  }
}

async function updateCategory(categoryId) {
  resetMessage()
  try {
    await api.put(`/api/admin/categories/${categoryId}`, categoryDrafts[categoryId])
    message.value = 'Категория обновлена'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить категорию'
  }
}

async function deleteCategory(categoryId) {
  if (!window.confirm('Скрыть эту категорию?')) {
    return
  }

  resetMessage()
  try {
    await api.delete(`/api/admin/categories/${categoryId}`)
    message.value = 'Категория скрыта'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось скрыть категорию'
  }
}

async function createCity() {
  resetMessage()
  try {
    await api.post('/api/admin/cities', cityForm)
    message.value = 'Город создан'
    cityForm.name_ru = ''
    cityForm.name_en = ''
    cityForm.name_kz = ''
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось создать город'
  }
}

async function updateCity(cityId) {
  resetMessage()
  try {
    await api.put(`/api/admin/cities/${cityId}`, cityDrafts[cityId])
    message.value = 'Город обновлен'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить город'
  }
}

async function deleteCity(cityId) {
  if (!window.confirm('Скрыть этот город?')) {
    return
  }

  resetMessage()
  try {
    await api.delete(`/api/admin/cities/${cityId}`)
    message.value = 'Город скрыт'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось скрыть город'
  }
}

async function createEvent() {
  resetMessage()
  try {
    const formData = new FormData()
    formData.append('title', eventForm.title)
    formData.append('description', eventForm.description)
    formData.append('video_url', eventForm.video_url)
    formData.append('category_id', eventForm.category_id)
    formData.append('city_id', eventForm.city_id)
    if (createPosterFile.value) {
      formData.append('poster', createPosterFile.value)
    }

    const createdEvent = await api.postForm('/api/admin/events/form', formData)
    selectedEventId.value = createdEvent.id
    message.value = 'Событие создано'
    resetCreateEventForm()
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось создать событие'
  }
}

async function updateEvent() {
  if (!selectedEvent.value) {
    return
  }

  resetMessage()
  try {
    await api.put(`/api/admin/events/${selectedEvent.value.id}`, {
      title: eventEdit.title,
      description: eventEdit.description || null,
      video_url: eventEdit.video_url || null,
      category_id: eventEdit.category_id || null,
      city_id: eventEdit.city_id || null
    })
    message.value = 'Событие обновлено'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить событие'
  }
}

async function uploadPoster() {
  if (!selectedEvent.value || !replacePosterFile.value) {
    return
  }

  resetMessage()
  try {
    const formData = new FormData()
    formData.append('poster', replacePosterFile.value)
    await api.postForm(`/api/admin/events/${selectedEvent.value.id}/poster`, formData)
    message.value = 'Постер обновлен'
    replacePosterFile.value = null
    setPreviewUrl(replacePosterPreviewUrl, null)
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить постер'
  }
}

async function deleteEvent() {
  if (!selectedEvent.value || !window.confirm('Скрыть это событие?')) {
    return
  }

  resetMessage()
  try {
    await api.delete(`/api/admin/events/${selectedEvent.value.id}`)
    message.value = 'Событие скрыто'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось скрыть событие'
  }
}

async function createSession() {
  if (!selectedEvent.value) {
    return
  }

  resetMessage()
  try {
    const startTime = toIsoDateTime(sessionForm.start_time)
    if (!startTime) {
      throw new Error('Укажи корректную дату и время сеанса')
    }

    const createdSession = await api.post(`/api/admin/events/${selectedEvent.value.id}/sessions`, {
      start_time: startTime,
      hall_name: sessionForm.hall_name,
      price: Number(sessionForm.price)
    })
    seatsForm.session_id = createdSession.id
    message.value = 'Сеанс создан'
    sessionForm.start_time = ''
    sessionForm.hall_name = ''
    sessionForm.price = ''
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось создать сеанс'
  }
}

async function updateSession(sessionId) {
  resetMessage()
  try {
    const startTime = toIsoDateTime(sessionDrafts[sessionId].start_time)
    if (!startTime) {
      throw new Error('Укажи корректную дату и время сеанса')
    }

    await api.put(`/api/admin/sessions/${sessionId}`, {
      start_time: startTime,
      hall_name: sessionDrafts[sessionId].hall_name,
      price: Number(sessionDrafts[sessionId].price)
    })
    message.value = 'Сеанс обновлен'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось обновить сеанс'
  }
}

async function deleteSession(sessionId) {
  if (!window.confirm('Скрыть этот сеанс?')) {
    return
  }

  resetMessage()
  try {
    await api.delete(`/api/admin/sessions/${sessionId}`)
    message.value = 'Сеанс скрыт'
    await loadReferenceData()
  } catch (err) {
    error.value = err.message || 'Не удалось скрыть сеанс'
  }
}

async function generateSeats(sessionId = seatsForm.session_id) {
  resetMessage()
  try {
    const payload = await api.post(`/api/admin/seats/generate/${sessionId}`, {
      rows: Number(seatsForm.rows),
      seats_per_row: Number(seatsForm.seats_per_row)
    })
    message.value = `Сгенерировано мест: ${payload.total_created}`
  } catch (err) {
    error.value = err.message || 'Не удалось сгенерировать места'
  }
}

watch(selectedEventId, syncSelectedEvent)

watch(filteredEvents, (nextEvents) => {
  if (!nextEvents.length) {
    return
  }

  if (!nextEvents.some((event) => event.id === selectedEventId.value)) {
    selectedEventId.value = nextEvents[0].id
  }
})

onMounted(async () => {
  theme.hydrate()
  await loadReferenceData()
})

onBeforeUnmount(() => {
  revokePreviewUrl(createPosterPreviewUrl.value)
  revokePreviewUrl(replacePosterPreviewUrl.value)
})
</script>

<template>
  <section class="space-y-6 sm:space-y-8">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <div class="eyebrow">Admin Studio</div>
        <h1 class="mt-3 font-display text-3xl sm:text-4xl" :class="headingClass">
          Управление каталогом, постерами и сеансами
        </h1>
        <p class="mt-4 max-w-3xl text-sm leading-7" :class="textMutedClass">
          Панель стала практичнее для ежедневной работы: можно искать события, менять город и
          категорию, редактировать дату сеанса, обновлять постеры и быстро генерировать схему мест.
        </p>
      </div>

      <button class="btn-secondary w-full sm:w-auto" @click="loadReferenceData">
        Обновить данные
      </button>
    </div>

    <div v-if="message" :class="[panelClass, theme.isDark.value ? 'p-5 text-sm text-emerald-200' : 'p-5 text-sm text-emerald-700']">
      {{ message }}
    </div>

    <div v-if="error" :class="[panelClass, theme.isDark.value ? 'p-5 text-sm text-rose-200' : 'p-5 text-sm text-rose-700']">
      {{ error }}
    </div>

    <div v-if="loading" class="space-y-4">
      <div
        v-for="index in 3"
        :key="index"
        class="h-40 animate-shimmer rounded-[2rem] bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%]"
      ></div>
    </div>

    <div v-else class="grid gap-6 xl:grid-cols-[1.18fr_0.82fr] xl:gap-8">
      <div class="space-y-6">
        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <div :class="metricCardClass">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Категории</div>
              <div class="mt-2 font-display text-3xl" :class="headingClass">{{ categories.length }}</div>
            </div>
            <div :class="metricCardClass">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Города</div>
              <div class="mt-2 font-display text-3xl" :class="headingClass">{{ cities.length }}</div>
            </div>
            <div :class="metricCardClass">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">События</div>
              <div class="mt-2 font-display text-3xl" :class="headingClass">{{ events.length }}</div>
            </div>
            <div :class="metricCardClass">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Сеансы</div>
              <div class="mt-2 font-display text-3xl" :class="headingClass">{{ totalSessions }}</div>
            </div>
            <div :class="metricCardClass">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Будущие</div>
              <div class="mt-2 font-display text-3xl" :class="headingClass">{{ upcomingSessions }}</div>
            </div>
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div class="eyebrow">Search & Filter</div>
              <h2 class="mt-2 font-display text-2xl" :class="headingClass">Поиск по событиям</h2>
            </div>
            <button class="btn-secondary w-full sm:w-auto" @click="resetEventFilters">Сбросить фильтры</button>
          </div>

          <div class="mt-6 grid gap-4 lg:grid-cols-[1.3fr_0.85fr_0.85fr]">
            <input
              v-model="eventSearch"
              class="field"
              placeholder="Название, город или категория"
            />
            <select v-model="eventCategoryFilter" class="field">
              <option value="">Все категории</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name_ru }}
              </option>
            </select>
            <select v-model="eventCityFilter" class="field">
              <option value="">Все города</option>
              <option v-for="city in cities" :key="city.id" :value="city.id">
                {{ city.name_ru }}
              </option>
            </select>
          </div>

          <div class="mt-5 flex flex-wrap gap-2">
            <button
              v-for="event in filteredEvents.slice(0, 16)"
              :key="event.id"
              :class="[
                chipButtonClass,
                selectedEventId === event.id
                  ? theme.isDark.value
                    ? 'border-sdu-copper/45 bg-sdu-copper/10 text-white'
                    : 'border-slate-900 bg-slate-900 text-white'
                  : ''
              ]"
              @click="selectedEventId = event.id"
            >
              {{ event.title }}
            </button>
          </div>

          <div
            v-if="!filteredEvents.length"
            class="mt-5 rounded-[1.25rem] border border-dashed px-4 py-5 text-sm"
            :class="theme.isDark.value ? 'border-white/10 text-sdu-mist/70' : 'border-slate-300 text-slate-500'"
          >
            По текущим фильтрам событий не найдено.
          </div>

          <div class="mt-4 text-sm" :class="textMutedClass">
            Найдено событий: {{ filteredEvents.length }}
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <div class="grid gap-6 lg:grid-cols-2">
            <form class="space-y-4" @submit.prevent="createCategory">
              <div class="eyebrow">Category</div>
              <h2 class="font-display text-2xl" :class="headingClass">Новая категория</h2>
              <input v-model="categoryForm.name_ru" class="field" placeholder="Название RU" required />
              <input v-model="categoryForm.name_en" class="field" placeholder="Name EN" required />
              <input v-model="categoryForm.name_kz" class="field" placeholder="Atauy KZ" required />
              <button class="btn-primary w-full">Создать категорию</button>
            </form>

            <form class="space-y-4" @submit.prevent="createCity">
              <div class="eyebrow">City</div>
              <h2 class="font-display text-2xl" :class="headingClass">Новый город</h2>
              <input v-model="cityForm.name_ru" class="field" placeholder="Город RU" required />
              <input v-model="cityForm.name_en" class="field" placeholder="City EN" required />
              <input v-model="cityForm.name_kz" class="field" placeholder="Qala KZ" required />
              <button class="btn-primary w-full">Создать город</button>
            </form>
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <form class="space-y-4" @submit.prevent="createEvent">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div class="eyebrow">Event</div>
                <h2 class="font-display text-2xl" :class="headingClass">Новое событие</h2>
              </div>
              <div class="text-sm" :class="textMutedClass">
                Используй эту форму для быстрого наполнения каталога реальными мероприятиями.
              </div>
            </div>
            <input v-model="eventForm.title" class="field" placeholder="Название события" required />
            <textarea
              v-model="eventForm.description"
              class="field min-h-28 resize-y"
              placeholder="Описание события"
            ></textarea>
            <input v-model="eventForm.video_url" class="field" placeholder="Video URL" />
            <div class="grid gap-4 md:grid-cols-2">
              <select v-model="eventForm.category_id" class="field" required>
                <option value="" disabled>Категория</option>
                <option v-for="category in categories" :key="category.id" :value="category.id">
                  {{ category.name_ru }}
                </option>
              </select>
              <select v-model="eventForm.city_id" class="field" required>
                <option value="" disabled>Город</option>
                <option v-for="city in cities" :key="city.id" :value="city.id">
                  {{ city.name_ru }}
                </option>
              </select>
            </div>
            <div class="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <div :class="[panelSoftClass, 'p-4']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Постер</div>
                <input type="file" accept="image/*" class="field mt-3" @change="onCreatePosterChange" />
                <div
                  class="mt-4 flex h-48 items-center justify-center overflow-hidden rounded-[1.25rem] border border-dashed"
                  :class="theme.isDark.value ? 'border-white/15 bg-white/5' : 'border-slate-300 bg-white'"
                >
                  <img
                    v-if="createPosterPreviewUrl"
                    :src="createPosterPreviewUrl"
                    alt="Poster preview"
                    class="h-full w-full object-cover"
                  />
                  <div v-else class="px-6 text-center text-sm" :class="textMutedClass">
                    Предпросмотр нового постера появится здесь
                  </div>
                </div>
              </div>

              <div :class="[panelSoftClass, 'p-4']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Подсказка</div>
                <ul class="mt-3 space-y-3 text-sm leading-6" :class="textMutedClass">
                  <li>Указывай точное название события, чтобы поиск на главной находил его быстрее.</li>
                  <li>Постер лучше загружать в вертикальном формате, чтобы карточки выглядели аккуратно.</li>
                  <li>После создания события можно сразу добавить сеансы и сгенерировать схему мест.</li>
                </ul>
              </div>
            </div>
            <button class="btn-primary">Создать событие</button>
          </form>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div class="eyebrow">Manage Event</div>
              <h2 class="mt-2 font-display text-2xl" :class="headingClass">Редактирование события</h2>
            </div>
            <select v-model="selectedEventId" class="field md:max-w-md">
              <option value="" disabled>Выбери событие</option>
              <option v-for="event in filteredEvents" :key="event.id" :value="event.id">
                {{ event.title }}
              </option>
            </select>
          </div>

          <div v-if="selectedEvent" class="mt-6 space-y-4">
            <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div :class="[metricCardClass, 'space-y-1']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Город</div>
                <div class="text-sm" :class="headingClass">{{ selectedEvent.city?.name_ru }}</div>
              </div>
              <div :class="[metricCardClass, 'space-y-1']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Категория</div>
                <div class="text-sm" :class="headingClass">{{ selectedEvent.category?.name_ru }}</div>
              </div>
              <div :class="[metricCardClass, 'space-y-1']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Сеансы</div>
                <div class="text-sm" :class="headingClass">{{ selectedEvent.sessions?.length || 0 }}</div>
              </div>
              <div :class="[metricCardClass, 'space-y-1']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Публичная страница</div>
                <RouterLink class="text-sm text-sdu-copper underline-offset-4 hover:underline" :to="`/events/${selectedEvent.id}`">
                  Открыть событие
                </RouterLink>
              </div>
            </div>

            <div class="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div class="space-y-4">
                <input v-model="eventEdit.title" class="field" placeholder="Название события" />
                <textarea v-model="eventEdit.description" class="field min-h-32 resize-y" placeholder="Описание"></textarea>
                <input v-model="eventEdit.video_url" class="field" placeholder="Video URL" />
                <div class="grid gap-4 md:grid-cols-2">
                  <select v-model="eventEdit.category_id" class="field">
                    <option value="" disabled>Категория</option>
                    <option v-for="category in categories" :key="category.id" :value="category.id">
                      {{ category.name_ru }}
                    </option>
                  </select>
                  <select v-model="eventEdit.city_id" class="field">
                    <option value="" disabled>Город</option>
                    <option v-for="city in cities" :key="city.id" :value="city.id">
                      {{ city.name_ru }}
                    </option>
                  </select>
                </div>
              </div>

              <div :class="[panelSoftClass, 'p-4']">
                <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Постер события</div>
                <div
                  class="mt-3 flex h-56 items-center justify-center overflow-hidden rounded-[1.25rem] border border-dashed"
                  :class="theme.isDark.value ? 'border-white/15 bg-white/5' : 'border-slate-300 bg-white'"
                >
                  <img
                    v-if="selectedEventPoster"
                    :src="selectedEventPoster"
                    :alt="selectedEvent.title"
                    class="h-full w-full object-cover"
                  />
                  <div
                    v-else
                    class="px-6 text-center text-sm"
                    :class="textMutedClass"
                  >
                    Постер еще не загружен
                  </div>
                </div>
                <input type="file" accept="image/*" class="field mt-4" @change="onReplacePosterChange" />
                <button class="btn-secondary mt-3 w-full" :disabled="!replacePosterFile" @click="uploadPoster">
                  Заменить постер
                </button>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <button class="btn-primary" @click="updateEvent">Сохранить событие</button>
              <button class="btn-secondary" @click="deleteEvent">Скрыть событие</button>
            </div>
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6 lg:p-8']">
          <div class="grid gap-6 lg:grid-cols-2">
            <form class="space-y-4" @submit.prevent="createSession">
              <div class="eyebrow">Session</div>
              <h2 class="font-display text-2xl" :class="headingClass">Новый сеанс</h2>
              <input v-model="sessionForm.start_time" type="datetime-local" class="field" required />
              <input v-model="sessionForm.hall_name" class="field" placeholder="Hall / Auditorium" required />
              <input v-model="sessionForm.price" type="number" min="0" class="field" placeholder="Цена" required />
              <button class="btn-primary w-full" :disabled="!selectedEventId">Создать сеанс для выбранного события</button>
            </form>

            <form class="space-y-4" @submit.prevent="generateSeats">
              <div class="eyebrow">Seats</div>
              <h2 class="font-display text-2xl" :class="headingClass">Генерация мест</h2>
              <select v-model="seatsForm.session_id" class="field" required>
                <option value="" disabled>Сеанс</option>
                <option v-for="session in selectedEventSessions" :key="session.id" :value="session.id">
                  {{ formatDateTime(session.start_time) }} · {{ session.hall_name }}
                </option>
              </select>
              <div class="grid gap-4 sm:grid-cols-2">
                <input v-model="seatsForm.rows" type="number" min="1" class="field" placeholder="Ряды" required />
                <input v-model="seatsForm.seats_per_row" type="number" min="1" class="field" placeholder="Мест в ряду" required />
              </div>
              <button class="btn-primary w-full" :disabled="!seatsForm.session_id">Сгенерировать места</button>
            </form>
          </div>
        </div>
      </div>

      <aside class="space-y-6">
        <div :class="[panelSoftClass, 'p-5 sm:p-6']">
          <div class="eyebrow">Categories</div>
          <div class="mt-4 space-y-3">
            <article
              v-for="category in categories"
              :key="category.id"
              :class="[metricCardClass, 'space-y-3']"
            >
              <div class="grid gap-3">
                <input v-model="categoryDrafts[category.id].name_ru" class="field" placeholder="Название RU" />
                <input v-model="categoryDrafts[category.id].name_en" class="field" placeholder="Name EN" />
                <input v-model="categoryDrafts[category.id].name_kz" class="field" placeholder="Atauy KZ" />
              </div>
              <div class="flex gap-2">
                <button class="btn-primary px-4 py-2 text-xs" @click="updateCategory(category.id)">Сохранить</button>
                <button class="btn-secondary px-4 py-2 text-xs" @click="deleteCategory(category.id)">Скрыть</button>
              </div>
            </article>
          </div>
        </div>

        <div :class="[panelSoftClass, 'p-5 sm:p-6']">
          <div class="eyebrow">Cities</div>
          <div class="mt-4 space-y-3">
            <article
              v-for="city in cities"
              :key="city.id"
              :class="[metricCardClass, 'space-y-3']"
            >
              <div class="grid gap-3">
                <input v-model="cityDrafts[city.id].name_ru" class="field" placeholder="Город RU" />
                <input v-model="cityDrafts[city.id].name_en" class="field" placeholder="City EN" />
                <input v-model="cityDrafts[city.id].name_kz" class="field" placeholder="Qala KZ" />
              </div>
              <div class="flex gap-2">
                <button class="btn-primary px-4 py-2 text-xs" @click="updateCity(city.id)">Сохранить</button>
                <button class="btn-secondary px-4 py-2 text-xs" @click="deleteCity(city.id)">Скрыть</button>
              </div>
            </article>
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6']">
          <div class="eyebrow">Sessions</div>
          <h2 class="mt-2 font-display text-2xl" :class="headingClass">
            Сеансы выбранного события
          </h2>
          <div v-if="!selectedEventSessions.length" class="mt-4 text-sm" :class="textMutedClass">
            Для этого события пока нет сеансов.
          </div>
          <div v-else class="mt-4 space-y-4">
            <article
              v-for="session in selectedEventSessions"
              :key="session.id"
              :class="[metricCardClass, 'space-y-3']"
            >
              <div class="text-xs uppercase tracking-[0.22em]" :class="textMutedClass">
                {{ formatDateTime(session.start_time) }}
              </div>
              <div class="grid gap-3">
                <input v-model="sessionDrafts[session.id].start_time" type="datetime-local" class="field" placeholder="Время сеанса" />
                <input v-model="sessionDrafts[session.id].hall_name" class="field" placeholder="Hall / Auditorium" />
                <input v-model="sessionDrafts[session.id].price" type="number" min="0" class="field" placeholder="Цена" />
              </div>
              <div class="text-sm" :class="textMutedClass">
                Текущая цена: {{ formatMoney(session.price) }}
              </div>
              <div class="flex flex-wrap gap-2">
                <button class="btn-primary px-4 py-2 text-xs" @click="updateSession(session.id)">Сохранить</button>
                <button class="btn-secondary px-4 py-2 text-xs" @click="generateSeats(session.id)">Места</button>
                <button class="btn-secondary px-4 py-2 text-xs" @click="deleteSession(session.id)">Скрыть</button>
              </div>
            </article>
          </div>
        </div>

        <div :class="[panelClass, 'p-5 sm:p-6']">
          <div class="eyebrow">Quick Event List</div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button
              v-for="event in filteredEvents.slice(0, 14)"
              :key="event.id"
              :class="chipButtonClass"
              @click="selectedEventId = event.id"
            >
              {{ event.title }}
            </button>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>
