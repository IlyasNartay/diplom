<script setup>
import { computed } from 'vue'

import { API_BASE_URL } from '@/lib/api'
import { normalizeAssetUrl, sessionPreview } from '@/lib/format'
import { useLanguageStore } from '@/stores/language'

const props = defineProps({
  event: {
    type: Object,
    required: true
  }
})

const language = useLanguageStore()
const locale = computed(() => (language.isRussian.value ? 'ru-RU' : 'en-US'))

const cardFallbackDescription = computed(() =>
  language.isRussian.value
    ? 'Кураторский отбор университетских мероприятий, концертов и специальных событий.'
    : 'A curated line-up of campus events, concerts, and special programmes.'
)

const detailsLabel = computed(() => (language.isRussian.value ? 'Подробнее' : 'Details'))

const posterUrl = computed(() => normalizeAssetUrl(props.event.poster_url, API_BASE_URL))
</script>

<template>
  <RouterLink
    :to="`/events/${event.id}`"
    class="group panel flex h-full flex-col overflow-hidden transition duration-300 hover:-translate-y-1 hover:border-sdu-copper/30"
  >
    <div class="relative h-56 overflow-hidden sm:h-64">
      <img
        v-if="posterUrl"
        :src="posterUrl"
        :alt="event.title"
        class="h-full w-full object-cover transition duration-700 group-hover:scale-105"
      />
      <div
        v-else
        class="flex h-full items-end bg-[linear-gradient(160deg,rgba(44,50,121,0.95),rgba(9,11,24,1))] p-6"
      >
        <div class="font-display text-3xl text-white/90">{{ event.title }}</div>
      </div>
      <div class="absolute inset-0 bg-[linear-gradient(180deg,transparent,rgba(9,11,24,0.76))]"></div>
      <div class="absolute left-4 top-4 rounded-full border border-white/10 bg-black/25 px-3 py-1 text-[0.68rem] uppercase tracking-[0.18em] text-sdu-copper/90 backdrop-blur sm:left-5 sm:top-5 sm:text-xs sm:tracking-[0.2em]">
        {{ event.category?.name_en || event.category?.name_ru }}
      </div>
    </div>

    <div class="flex flex-1 flex-col gap-4 p-5 sm:p-6">
      <div>
        <div class="text-xs uppercase tracking-[0.22em] text-sdu-mist/65">{{ event.city?.name_en || event.city?.name_ru }}</div>
        <h3 class="mt-2 font-display text-xl text-white sm:text-2xl">{{ event.title }}</h3>
      </div>

      <p class="max-h-[4.5rem] overflow-hidden text-sm leading-6 text-sdu-mist/75">
        {{ event.description || cardFallbackDescription }}
      </p>

      <div class="mt-auto flex flex-col items-start gap-2 sm:flex-row sm:items-end sm:justify-between sm:gap-3">
        <div class="text-sm text-sdu-mist/80">
          {{ sessionPreview(event, locale) }}
        </div>
        <span class="text-xs uppercase tracking-[0.22em] text-sdu-copper">{{ detailsLabel }}</span>
      </div>
    </div>
  </RouterLink>
</template>
