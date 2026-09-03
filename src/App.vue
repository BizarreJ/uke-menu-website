<script setup>
import { computed, onMounted, ref, watch } from "vue";
import DayPicker from "./components/DayPicker.vue";
import MenuCard from "./components/MenuCard.vue";

const filters = [
  { id: "alle", label: "Alle" },
  { id: "vegan", label: "Vegan" },
  { id: "vegetarisch", label: "Vegetarisch" },
  { id: "fleisch/fisch", label: "Fleisch & Fisch" },
];

const savedFilter = localStorage.getItem("uke-menu-filter");
const validFilter = filters.some((filter) => filter.id === savedFilter) ? savedFilter : "alle";
const menuData = ref(null);
const selectedDate = ref("");
const activeFilter = ref(validFilter);
const loading = ref(true);
const error = ref("");
const toast = ref("");
let toastTimer;

const dates = computed(() => menuData.value ? Object.keys(menuData.value.tage) : []);
const selectedDay = computed(() => menuData.value?.tage[selectedDate.value]);
const meals = computed(() => {
  const items = selectedDay.value?.gerichte || [];
  return activeFilter.value === "alle"
    ? items
    : items.filter((item) => item.ernaehrungsform === activeFilter.value);
});

const weekRange = computed(() => {
  if (!menuData.value) return "";
  const format = new Intl.DateTimeFormat("de-DE", { day: "numeric", month: "long" });
  const from = format.format(parseDate(menuData.value.zeitraum_von));
  const to = new Intl.DateTimeFormat("de-DE", {
    day: "numeric", month: "long", year: "numeric",
  }).format(parseDate(menuData.value.zeitraum_bis));
  return `${from} – ${to}`;
});

watch(activeFilter, (value) => localStorage.setItem("uke-menu-filter", value));

function parseDate(value) {
  return new Date(`${value}T12:00:00`);
}

function localDateKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function showToast(message) {
  clearTimeout(toastTimer);
  toast.value = message;
  toastTimer = setTimeout(() => { toast.value = ""; }, 2200);
}

onMounted(async () => {
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/speiseplan.json`, {
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    menuData.value = await response.json();
    const today = localDateKey();
    selectedDate.value = menuData.value.tage[today] ? today : dates.value[0];
  } catch (reason) {
    console.error(reason);
    error.value = "Der Speiseplan konnte nicht geladen werden.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <div>
          <p class="overline">UKE Kantine</p>
          <h1>Menü</h1>
        </div>
        <div class="week-pill" aria-live="polite">
          <span class="live-dot" aria-hidden="true"></span>
          {{ weekRange || "Aktueller Plan" }}
        </div>
      </div>
    </header>

    <main>
      <section class="controls" aria-label="Speiseplan auswählen">
        <DayPicker
          v-if="dates.length"
          :dates="dates"
          :days="menuData.tage"
          :selected="selectedDate"
          @select="selectedDate = $event"
        />

        <div class="filter-row" aria-label="Gerichte filtern">
          <button
            v-for="filter in filters"
            :key="filter.id"
            type="button"
            class="filter-chip"
            :class="{ active: activeFilter === filter.id }"
            :aria-pressed="activeFilter === filter.id"
            @click="activeFilter = filter.id"
          >
            {{ filter.label }}
          </button>
        </div>
      </section>

      <section class="menu-section" aria-live="polite">
        <div v-if="selectedDay" class="day-heading">
          <div>
            <p class="section-label">{{ selectedDay.wochentag }}</p>
            <h2>{{ meals.length }} {{ meals.length === 1 ? "Gericht" : "Gerichte" }}</h2>
          </div>
          <span class="date-label">
            {{ new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit" }).format(parseDate(selectedDate)) }}
          </span>
        </div>

        <p v-if="loading" class="state-card">Speiseplan wird geladen …</p>
        <p v-else-if="error" class="state-card error">{{ error }}</p>
        <p v-else-if="!meals.length" class="state-card">
          Für diesen Filter gibt es heute kein Gericht.
        </p>

        <div v-else class="menu-grid">
          <MenuCard
            v-for="meal in meals"
            :key="`${selectedDate}-${meal['menü']}`"
            :meal="meal"
            @copied="showToast('Kopiert')"
            @copy-error="showToast('Kopieren nicht möglich')"
          />
        </div>
      </section>
    </main>

    <Transition name="toast">
      <div v-if="toast" class="toast" role="status">{{ toast }}</div>
    </Transition>
  </div>
</template>
