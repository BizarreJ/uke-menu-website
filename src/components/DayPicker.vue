<script setup>
defineProps({
  dates: { type: Array, required: true },
  days: { type: Object, required: true },
  selected: { type: String, required: true },
});

defineEmits(["select"]);

function dateNumber(value) {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit" })
    .format(new Date(`${value}T12:00:00`));
}
</script>

<template>
  <nav class="day-picker" aria-label="Wochentag">
    <button
      v-for="date in dates"
      :key="date"
      type="button"
      class="day-button"
      :class="{ active: selected === date }"
      :aria-current="selected === date ? 'date' : undefined"
      @click="$emit('select', date)"
    >
      <span>{{ days[date].wochentag.slice(0, 2) }}</span>
      <strong>{{ dateNumber(date) }}</strong>
    </button>
  </nav>
</template>
