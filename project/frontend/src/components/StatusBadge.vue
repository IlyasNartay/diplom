<script setup>
import { computed } from 'vue'

import { useLanguageStore } from '@/stores/language'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
const language = useLanguageStore()

const props = defineProps({
  status: {
    type: String,
    default: ''
  }
})

const labels = {
  ru: {
    completed: 'Завершено',
    payment_failed: 'Оплата отклонена',
    payment_pending: 'Ожидает оплаты',
    seat_reserved: 'Места удержаны',
    seat_reservation_failed: 'Бронь не удалась',
    payment_success: 'Оплата принята',
    started: 'Запущено',
    unknown: 'Неизвестно'
  },
  en: {
    completed: 'Completed',
    payment_failed: 'Payment declined',
    payment_pending: 'Payment pending',
    seat_reserved: 'Seats held',
    seat_reservation_failed: 'Reservation failed',
    payment_success: 'Payment received',
    started: 'Started',
    unknown: 'Unknown'
  }
}

const view = computed(() => {
  const lang = language.isRussian.value ? 'ru' : 'en'
  const L = labels[lang]

  const map = {
    completed: {
      label: L.completed,
      classes: theme.isDark
        ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700'
    },
    payment_failed: {
      label: L.payment_failed,
      classes: theme.isDark
        ? 'border-rose-400/30 bg-rose-400/10 text-rose-200'
        : 'border-rose-200 bg-rose-50 text-rose-700'
    },
    payment_pending: {
      label: L.payment_pending,
      classes: theme.isDark
        ? 'border-amber-300/30 bg-amber-300/10 text-amber-100'
        : 'border-amber-200 bg-amber-50 text-amber-700'
    },
    seat_reserved: {
      label: L.seat_reserved,
      classes: theme.isDark
        ? 'border-sky-400/30 bg-sky-400/10 text-sky-200'
        : 'border-sky-200 bg-sky-50 text-sky-700'
    },
    seat_reservation_failed: {
      label: L.seat_reservation_failed,
      classes: theme.isDark
        ? 'border-rose-400/30 bg-rose-400/10 text-rose-200'
        : 'border-rose-200 bg-rose-50 text-rose-700'
    },
    payment_success: {
      label: L.payment_success,
      classes: theme.isDark
        ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700'
    },
    started: {
      label: L.started,
      classes: theme.isDark
        ? 'border-white/15 bg-white/10 text-white'
        : 'border-slate-200 bg-slate-50 text-slate-700'
    }
  }

  return (
    map[props.status] || {
      label: props.status || L.unknown,
      classes: theme.isDark
        ? 'border-white/15 bg-white/10 text-white'
        : 'border-slate-200 bg-slate-50 text-slate-700'
    }
  )
})
</script>

<template>
  <span
    class="inline-flex rounded-full border px-3 py-1 text-xs uppercase tracking-[0.18em]"
    :class="view.classes"
  >
    {{ view.label }}
  </span>
</template>
