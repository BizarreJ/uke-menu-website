<script setup>
import { computed } from "vue";

const props = defineProps({
  meal: { type: Object, required: true },
});
const emit = defineEmits(["copied", "copy-error"]);

const dietLabel = computed(() => ({
  vegan: "Vegan",
  vegetarisch: "Vegetarisch",
  "fleisch/fisch": "Fleisch / Fisch",
}[props.meal.ernaehrungsform] || "Nicht zugeordnet"));

const proteins = computed(() => (props.meal.proteintypen || [])
  .map((word) => word[0].toUpperCase() + word.slice(1))
  .join(" + "));

const allergenNames = {
  A: "Glutenhaltiges Getreide",
  B: "Krebstiere",
  C: "Eier",
  D: "Fisch",
  E: "Erdnüsse",
  F: "Soja",
  G: "Milch (einschließlich Laktose)",
  H: "Schalenfrüchte",
  I: "Sellerie",
  J: "Senf",
  K: "Sesamsamen",
  L: "Schwefeldioxid und Sulphite",
  M: "Lupinen",
  N: "Weichtiere",
};

const allergens = computed(() => props.meal.allergene?.length
  ? props.meal.allergene
    .map((code) => allergenNames[code] || `Unbekannt (${code})`)
    .join(" · ")
  : "keine Angabe");

function formatPrice(value) {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

async function copyText() {
  const text = `${props.meal.beschreibung}. Portion laut UKE-Casino ca. ${props.meal.kcal} kcal.`;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.cssText = "position:fixed;opacity:0";
      document.body.append(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    emit("copied");
  } catch {
    emit("copy-error");
  }
}
</script>

<template>
  <article class="menu-card">
    <div class="card-meta">
      <span class="menu-name">{{ meal["menü"] }}</span>
      <span class="diet-badge" :class="meal.ernaehrungsform.replace('/', '-')">
        {{ dietLabel }}
      </span>
    </div>

    <h3>{{ meal.gericht }}</h3>
    <p class="description">{{ meal.beschreibung.replaceAll(" / ", " · ") }}</p>

    <div class="nutrition-line">
      <strong>{{ meal.kcal.toLocaleString("de-DE") }} kcal</strong>
      <span v-if="proteins">{{ proteins }}</span>

    <button
        type="button"
        class="copy-button"
        aria-label="Kopieren"
        title="Kopieren"
        @click="copyText"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M8 7V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2M5 8h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
        </svg>
    </button>
</div>

    <dl class="details-grid">
      <div>
        <dt>Intern</dt>
        <dd>{{ formatPrice(meal.preis_intern_eur) }}</dd>
      </div>
      <div>
        <dt>Extern</dt>
        <dd>{{ formatPrice(meal.preis_extern_eur) }}</dd>
      </div>
      <div class="allergen-detail">
        <dt>Allergene</dt>
        <dd>{{ allergens }}</dd>
      </div>
    </dl>
  </article>
</template>
