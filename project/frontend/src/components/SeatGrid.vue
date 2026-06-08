<script setup>
import { computed } from 'vue'

import { formatMoney } from '@/lib/format'
import { useThemeStore } from '@/stores/theme'

const props = defineProps({
  seats: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])
const theme = useThemeStore()
const isDark = computed(() => theme.isDark)

const groupedSeats = computed(() => {
  const grouped = new Map()

  for (const seat of props.seats) {
    if (!grouped.has(seat.row)) {
      grouped.set(seat.row, [])
    }
    grouped.get(seat.row).push(seat)
  }

  return [...grouped.entries()].map(([row, seats]) => ({
    row,
    seats: [...seats].sort((a, b) => Number(a.number) - Number(b.number))
  }))
})

const maxSeatsPerRow = computed(() =>
  groupedSeats.value.reduce((max, group) => Math.max(max, group.seats.length), 0)
)

function isSelected(seat) {
  return props.modelValue.includes(seat.id)
}

function toggleSeat(seat) {
  if (seat.status !== 'free') {
    return
  }

  const next = isSelected(seat)
    ? props.modelValue.filter((item) => item !== seat.id)
    : [...props.modelValue, seat.id]

  emit('update:modelValue', next)
}

function seatClasses(seat) {
  if (seat.status === 'sold') {
    return isDark.value
      ? 'border-rose-400/20 bg-rose-500/20 text-rose-100 cursor-not-allowed'
      : 'border-rose-200 bg-rose-50 text-rose-600 cursor-not-allowed'
  }
  if (seat.status === 'reserved') {
    return isDark.value
      ? 'border-amber-300/20 bg-amber-400/20 text-amber-50 cursor-not-allowed'
      : 'border-amber-200 bg-amber-50 text-amber-700 cursor-not-allowed'
  }
  if (isSelected(seat)) {
    return 'border-sdu-copper bg-sdu-copper text-sdu-night shadow-copper'
  }
  return isDark.value
    ? 'border-white/10 bg-white/5 text-white hover:border-sdu-copper/60 hover:bg-white/10'
    : 'border-slate-200 bg-white text-slate-700 hover:border-sdu-copper/50 hover:bg-amber-50'
}
</script>

<template>
  <div class="space-y-4 sm:space-y-5">
    <div
      class="rounded-[1.25rem] px-4 py-3 text-center text-[0.68rem] uppercase tracking-[0.28em] sm:rounded-[1.4rem] sm:text-xs sm:tracking-[0.34em]"
      :class="
        isDark
          ? 'border border-sdu-copper/20 bg-[linear-gradient(180deg,rgba(241,168,109,0.18),rgba(241,168,109,0.04))] text-sdu-copper/90'
          : 'border border-amber-200 bg-[linear-gradient(180deg,rgba(251,191,36,0.16),rgba(251,191,36,0.04))] text-sdu-royal'
      "
    >
      Stage / Screen
    </div>

    <div
      class="rounded-[1.5rem] p-3 sm:p-4"
      :class="isDark ? 'bg-sdu-night/60 ring-1 ring-white/10' : 'bg-slate-50 ring-1 ring-slate-200'"
    >
      <div
        class="mx-auto mb-4 h-2 w-40 rounded-full sm:w-56"
        :class="isDark ? 'bg-white/10' : 'bg-slate-200'"
      ></div>

      <div class="space-y-2.5 sm:space-y-3">
        <div
          v-for="group in groupedSeats"
          :key="group.row"
          class="grid grid-cols-[2rem_1fr] items-center gap-2 sm:grid-cols-[3rem_1fr] sm:gap-3"
        >
          <div
            class="text-center text-[0.62rem] font-semibold uppercase tracking-[0.2em] sm:text-xs"
            :class="isDark ? 'text-sdu-mist/60' : 'text-slate-500'"
          >
            {{ group.row }}
          </div>
          <div
            class="grid gap-1.5 sm:gap-2"
            :style="{ gridTemplateColumns: `repeat(${Math.max(maxSeatsPerRow, group.seats.length)}, minmax(0, 1fr))` }"
          >
            <button
              v-for="seat in group.seats"
              :key="seat.id"
              type="button"
              class="aspect-square min-h-[2.15rem] rounded-[0.95rem] border px-0.5 py-0.5 text-center text-[0.64rem] font-semibold transition sm:min-h-[2.7rem] sm:rounded-[1.05rem] sm:text-[0.72rem]"
              :class="seatClasses(seat)"
              @click="toggleSeat(seat)"
            >
              <div>{{ seat.number }}</div>
              <div class="mt-0.5 hidden text-[0.56rem] opacity-75 sm:block">{{ formatMoney(seat.price) }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
