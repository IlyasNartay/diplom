<script setup>
import { computed } from 'vue'

import { formatMoney, normalizeAssetUrl } from '@/lib/format'
import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const props = defineProps({
  event: {
    type: Object,
    required: true
  }
})

const language = useLanguageStore()
const theme = useThemeStore()

language.hydrate()
theme.hydrate()

const labelMap = {
  Concerts: { ru: 'Концерты', en: 'Concerts' },
  Festivals: { ru: 'Фестивали', en: 'Festivals' },
  Classical: { ru: 'Классика', en: 'Classical' },
  Almaty: { ru: 'Алматы', en: 'Almaty' },
  Astana: { ru: 'Астана', en: 'Astana' },
  Konaev: { ru: 'Конаев', en: 'Konaev' }
}

const shortDateFormatter = computed(() =>
  new Intl.DateTimeFormat(language.isRussian.value ? 'ru-RU' : 'en-US', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
)

const t = computed(() => {
  if (language.isRussian.value) {
    return {
      details: 'Подробнее',
      from: 'от',
      dateTbd: 'Дата уточняется',
      fallback: 'Подробности и расписание уже доступны на странице события.'
    }
  }

  return {
    details: 'Details',
    from: 'from',
    dateTbd: 'Date to be confirmed',
    fallback: 'Details and schedule are already available on the event page.'
  }
})

const posterUrl = computed(() => normalizeAssetUrl(props.event.poster_url || '', ''))
const nextSession = computed(
  () => [...(props.event.sessions || [])].sort((left, right) => new Date(left.start_time) - new Date(right.start_time))[0] || null
)

function displayLabel(value) {
  const key = language.isRussian.value ? 'ru' : 'en'
  return labelMap[value]?.[key] || value
}
</script>

<template>
  <RouterLink
    :to="`/events/${event.id}`"
    class="group overflow-hidden rounded-[1.8rem] shadow-[0_24px_60px_rgba(15,23,42,0.08)] ring-1 transition duration-300 hover:-translate-y-1 hover:shadow-[0_28px_80px_rgba(15,23,42,0.14)]"
    :class="theme.isDark ? 'bg-white/5 ring-white/10' : 'bg-white ring-slate-200'"
  >
    <div class="relative h-72 overflow-hidden">
      <img
        v-if="posterUrl"
        :src="posterUrl"
        :alt="event.title"
        class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
      />
      <div
        v-else
        class="flex h-full items-end bg-[linear-gradient(160deg,#0f172a,#334155)] p-5 text-white"
      >
        <div class="font-display text-3xl">{{ event.title }}</div>
      </div>
      <div class="absolute inset-0 bg-[linear-gradient(180deg,transparent,rgba(15,23,42,0.3))]"></div>
      <div
        class="absolute left-4 top-4 rounded-full px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em]"
        :class="theme.isDark ? 'bg-sdu-night/80 text-sdu-copper backdrop-blur-sm' : 'bg-white/90 text-slate-900'"
      >
        {{ displayLabel(event.category?.name_ru) }}
      </div>
    </div>

    <div class="flex flex-1 flex-col gap-4 p-5">
      <div>
        <h3 class="text-2xl font-semibold leading-tight" :class="theme.isDark ? 'text-white' : 'text-slate-950'">
          {{ event.title }}
        </h3>
        <p class="mt-3 max-h-[4.5rem] overflow-hidden text-sm leading-6" :class="theme.isDark ? 'text-slate-300' : 'text-slate-500'">
          {{ event.description || t.fallback }}
        </p>
      </div>

      <div class="space-y-2 text-sm" :class="theme.isDark ? 'text-slate-300' : 'text-slate-600'">
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-4 w-4" :class="theme.isDark ? 'text-slate-500' : 'text-slate-400'" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M8 2v4"></path>
            <path d="M16 2v4"></path>
            <rect width="18" height="18" x="3" y="4" rx="2"></rect>
            <path d="M3 10h18"></path>
          </svg>
          <span>{{ nextSession ? shortDateFormatter.format(new Date(nextSession.start_time)) : t.dateTbd }}</span>
        </div>
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="h-4 w-4" :class="theme.isDark ? 'text-slate-500' : 'text-slate-400'" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 21s7-4.35 7-11a7 7 0 1 0-14 0c0 6.65 7 11 7 11Z"></path>
            <circle cx="12" cy="10" r="2.5"></circle>
          </svg>
          <span>{{ displayLabel(event.city?.name_ru) }}{{ nextSession?.hall_name ? `, ${nextSession.hall_name}` : '' }}</span>
        </div>
      </div>

      <div class="mt-auto flex items-center justify-between gap-3">
        <div class="text-sm font-semibold" :class="theme.isDark ? 'text-sdu-copper' : 'text-emerald-700'">
          {{ nextSession ? `${t.from} ${formatMoney(nextSession.price)}` : 'Soon' }}
        </div>
        <span
          class="rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em]"
          :class="theme.isDark ? 'bg-white/10 text-slate-200' : 'bg-slate-100 text-slate-600'"
        >
          {{ t.details }}
        </span>
      </div>
    </div>
  </RouterLink>
</template>

