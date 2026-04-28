<script setup>
import { computed } from 'vue'

import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

const props = defineProps({
  status: {
    type: String,
    default: ''
  }
})

const view = computed(() => {
  const map = {
    completed: {
      label: 'Завершено',
      classes: theme.isDark.value
        ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700'
    },
    payment_failed: {
      label: 'Оплата отклонена',
      classes: theme.isDark.value
        ? 'border-rose-400/30 bg-rose-400/10 text-rose-200'
        : 'border-rose-200 bg-rose-50 text-rose-700'
    },
    payment_pending: {
      label: 'Ожидает оплаты',
      classes: theme.isDark.value
        ? 'border-amber-300/30 bg-amber-300/10 text-amber-100'
        : 'border-amber-200 bg-amber-50 text-amber-700'
    },
    seat_reserved: {
      label: 'Места удержаны',
      classes: theme.isDark.value
        ? 'border-sky-400/30 bg-sky-400/10 text-sky-200'
        : 'border-sky-200 bg-sky-50 text-sky-700'
    },
    seat_reservation_failed: {
      label: 'Бронь не удалась',
      classes: theme.isDark.value
        ? 'border-rose-400/30 bg-rose-400/10 text-rose-200'
        : 'border-rose-200 bg-rose-50 text-rose-700'
    },
    payment_success: {
      label: 'Оплата принята',
      classes: theme.isDark.value
        ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700'
    },
    started: {
      label: 'Запущено',
      classes: theme.isDark.value
        ? 'border-white/15 bg-white/10 text-white'
        : 'border-slate-200 bg-slate-50 text-slate-700'
    }
  }

  return map[props.status] || {
    label: props.status || 'Неизвестно',
    classes: theme.isDark.value
      ? 'border-white/15 bg-white/10 text-white'
      : 'border-slate-200 bg-slate-50 text-slate-700'
  }
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

