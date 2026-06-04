<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import EventCard from '@/components/EventCard.vue'
import { api } from '@/lib/api'

const events = ref([])
const categories = ref([])
const cities = ref([])
const filters = ref({
  category_id: '',
  city_id: ''
})
const loading = ref(true)
const error = ref('')

async function loadFilters() {
  const [categoryPayload, cityPayload] = await Promise.all([
    api.get('/api/categories'),
    api.get('/api/cities')
  ])
  categories.value = categoryPayload
  cities.value = cityPayload
}

async function loadEvents() {
  loading.value = true
  error.value = ''

  const params = new URLSearchParams()
  if (filters.value.category_id) {
    params.set('category_id', filters.value.category_id)
  }
  if (filters.value.city_id) {
    params.set('city_id', filters.value.city_id)
  }

  const query = params.toString()
  try {
    const payload = await api.get(`/api/events${query ? `?${query}` : ''}`)
    events.value = payload.events || []
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить каталог'
  } finally {
    loading.value = false
  }
}

const activeFilterLabel = computed(() => {
  const city = cities.value.find((item) => item.id === filters.value.city_id)
  const category = categories.value.find((item) => item.id === filters.value.category_id)
  if (!city && !category) {
    return 'Все университетские события'
  }
  return [category?.name_ru, city?.name_ru].filter(Boolean).join(' · ')
})

watch(
  () => ({ ...filters.value }),
  () => {
    loadEvents()
  }
)

onMounted(async () => {
  try {
    await loadFilters()
    await loadEvents()
  } catch (err) {
    error.value = err.message || 'Ошибка при инициализации'
    loading.value = false
  }
})
</script>

<template>
  <section class="grid gap-6 lg:grid-cols-[1.3fr_0.7fr] lg:gap-8">
    <div class="panel overflow-hidden p-6 sm:p-8 lg:p-10">
      <div class="grid gap-6 xl:grid-cols-[1.08fr_0.92fr] xl:items-center xl:gap-8">
        <div>
          <div class="eyebrow">SDU University Experience</div>
          <h1 class="headline mt-4 max-w-3xl animate-fade-up">
            Билеты на кампусные события в более
            <span class="text-sdu-copper">цельном, спокойном и премиальном</span>
            формате.
          </h1>
          <p class="mt-5 max-w-2xl text-sm leading-7 text-sdu-mist/75 sm:mt-6 sm:text-lg sm:leading-8">
            Frontend for the high-load ticket booking system: event discovery, sessions, seat selection, checkout, and booking history
            в палитре, вдохновлённой фирменной айдентикой SDU.
          </p>

          <div class="mt-7 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap">
            <a href="#catalog" class="btn-primary w-full sm:w-auto">Смотреть афишу</a>
            <RouterLink to="/history" class="btn-secondary w-full sm:w-auto">Мои бронирования</RouterLink>
          </div>

          <div class="mt-8 grid gap-3 sm:mt-10 sm:grid-cols-3 sm:gap-4">
            <div class="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Каталог</div>
              <div class="mt-3 font-display text-3xl text-white">{{ events.length }}</div>
              <div class="text-sm text-sdu-mist/70">событий в текущей выдаче</div>
            </div>
            <div class="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">PWA</div>
              <div class="mt-3 font-display text-3xl text-white">Install</div>
              <div class="text-sm text-sdu-mist/70">быстрый доступ с домашнего экрана</div>
            </div>
            <div class="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-sdu-copper/75">Маршрут</div>
              <div class="mt-3 font-display text-3xl text-white">Saga</div>
              <div class="text-sm text-sdu-mist/70">seat → order → payment → ticket</div>
            </div>
          </div>
        </div>

        <div class="relative overflow-hidden rounded-[1.6rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-5 sm:rounded-[2rem] sm:p-8">
          <div class="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top,rgba(241,168,109,0.22),transparent_70%)]"></div>
          <div class="relative">
            <div class="text-center">
              <div class="text-xs uppercase tracking-[0.28em] text-sdu-copper/80">Official Identity</div>
              <img
                src="/branding/logo_sdu.png"
                alt="SDU University logo"
                class="mx-auto mt-4 w-full max-w-[14rem] object-contain drop-shadow-[0_28px_70px_rgba(0,0,0,0.45)] sm:mt-5 sm:max-w-[23rem]"
              />
            </div>
            <div class="mt-5 rounded-[1.3rem] border border-white/10 bg-black/20 p-4 text-sm leading-7 text-sdu-mist/78 sm:mt-6 sm:rounded-[1.5rem] sm:p-5">
              Визуальная система фронтенда уже опирается на реальный знак SDU: тёмный фон, глубокие синие тона,
              медный акцент и более сдержанная академическая композиция вместо стандартного продуктового шаблона.
            </div>
          </div>
        </div>
      </div>
    </div>

    <aside class="panel-soft p-5 sm:p-8">
      <div class="eyebrow">Фильтрация</div>
      <h2 class="mt-3 font-display text-3xl text-white">Подобрать событие</h2>
      <p class="mt-3 text-sm leading-7 text-sdu-mist/75">
        Используй фильтры по городу и категории. Дальше можно открыть мероприятие, выбрать сеанс и перейти к местам.
      </p>

      <div class="mt-6 space-y-4">
        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Категория</label>
          <select v-model="filters.category_id" class="field">
            <option value="">Все категории</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name_ru }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-2 block text-xs uppercase tracking-[0.24em] text-sdu-mist/65">Город</label>
          <select v-model="filters.city_id" class="field">
            <option value="">Все города</option>
            <option v-for="city in cities" :key="city.id" :value="city.id">
              {{ city.name_ru }}
            </option>
          </select>
        </div>
      </div>

      <div class="mt-6 rounded-[1.3rem] border border-sdu-copper/15 bg-sdu-copper/10 p-4 sm:mt-8 sm:rounded-[1.5rem]">
        <div class="text-xs uppercase tracking-[0.24em] text-sdu-copper/80">Текущая подборка</div>
        <div class="mt-2 text-lg text-white">{{ activeFilterLabel }}</div>
      </div>
    </aside>
  </section>

  <section id="catalog" class="mt-8 sm:mt-10">
    <div class="mb-5 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div class="eyebrow">Event Catalog</div>
        <h2 class="mt-2 font-display text-4xl text-white">Афиша</h2>
      </div>
      <p class="max-w-xl text-sm leading-7 text-sdu-mist/70">
        Карточки строятся на данных `catalog_service`, а покупка продолжается через `orchestrator` и event-driven saga.
      </p>
    </div>

    <div v-if="error" class="panel p-5 text-sm text-rose-200">
      {{ error }}
    </div>

    <div
      v-else-if="loading"
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <div
        v-for="index in 6"
        :key="index"
        class="panel h-[27rem] overflow-hidden bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08),rgba(255,255,255,0.04))] bg-[length:200%_100%] animate-shimmer"
      ></div>
    </div>

    <div v-else-if="!events.length" class="panel p-6 text-center sm:p-8">
      <div class="font-display text-3xl text-white">Ничего не найдено</div>
      <p class="mt-3 text-sm text-sdu-mist/75">
        Попробуй убрать фильтры или добавь мероприятия через `catalog_service`.
      </p>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <EventCard v-for="event in events" :key="event.id" :event="event" />
    </div>
  </section>
</template>
