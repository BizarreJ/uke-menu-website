<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  menuData: { type: Object, default: null },
});
const emit = defineEmits(["notice"]);

const STORAGE_KEY = "uke-menu-transactions-v1";

function loadTransactions() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

const transactions = ref(loadTransactions());
const depositAmount = ref("");
const expenseAmount = ref("");
const expenseDescription = ref("");
const expenseDate = ref(localDateKey());
const mealDate = ref("");
const selectedMealIndex = ref("");
const importInput = ref(null);

const dates = computed(() => props.menuData ? Object.keys(props.menuData.tage) : []);
const mealsForDate = computed(() => props.menuData?.tage[mealDate.value]?.gerichte || []);
const selectedMeal = computed(() => selectedMealIndex.value === ""
  ? null
  : mealsForDate.value[Number(selectedMealIndex.value)]);
const balance = computed(() => transactions.value.reduce(
  (sum, transaction) => sum + Number(transaction.amount),
  0,
));
const sortedTransactions = computed(() => [...transactions.value].sort((a, b) =>
  String(b.createdAt || b.date).localeCompare(String(a.createdAt || a.date))
));

watch(transactions, (value) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}, { deep: true });

watch(dates, (value) => {
  if (!value.length || mealDate.value) return;
  const today = localDateKey();
  mealDate.value = value.includes(today) ? today : value[0];
}, { immediate: true });

watch(mealDate, () => { selectedMealIndex.value = ""; });

function localDateKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseAmount(value) {
  return Number(String(value).replace(",", "."));
}

function makeId() {
  return crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function addTransaction(transaction) {
  transactions.value.push({
    id: makeId(),
    createdAt: new Date().toISOString(),
    ...transaction,
  });
}

function addDeposit() {
  const amount = parseAmount(depositAmount.value);
  if (!Number.isFinite(amount) || amount <= 0) return emit("notice", "Bitte einen gültigen Betrag eingeben");
  addTransaction({ type: "deposit", date: localDateKey(), amount });
  depositAmount.value = "";
  emit("notice", "Einzahlung gespeichert");
}

function addExpense() {
  const amount = parseAmount(expenseAmount.value);
  if (!Number.isFinite(amount) || amount <= 0) return emit("notice", "Bitte einen gültigen Betrag eingeben");
  addTransaction({
    type: "expense",
    date: expenseDate.value || localDateKey(),
    amount: -amount,
    description: expenseDescription.value.trim() || "Manuelle Ausgabe",
  });
  expenseAmount.value = "";
  expenseDescription.value = "";
  emit("notice", "Ausgabe gespeichert");
}

function addMeal() {
  const meal = selectedMeal.value;
  if (!meal) return emit("notice", "Bitte ein Menü auswählen");
  addTransaction({
    type: "meal",
    date: mealDate.value,
    amount: -Number(meal.preis_intern_eur),
    menu: meal["menü"],
    dish: meal.gericht,
  });
  selectedMealIndex.value = "";
  emit("notice", "Menü abgebucht");
}

function removeTransaction(id) {
  transactions.value = transactions.value.filter((item) => item.id !== id);
  emit("notice", "Buchung gelöscht");
}

function formatMoney(value) {
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(value) {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
    .format(new Date(`${value}T12:00:00`));
}

function transactionTitle(item) {
  if (item.type === "deposit") return "Einzahlung";
  if (item.type === "meal") return `${item.menu}: ${item.dish}`;
  return item.description || "Manuelle Ausgabe";
}

function exportTransactions() {
  const blob = new Blob([JSON.stringify(transactions.value, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `uke-kartenguthaben-${localDateKey()}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importTransactions(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const imported = JSON.parse(await file.text());
    if (!Array.isArray(imported) || imported.some((item) =>
      !item || typeof item.id !== "string" || !Number.isFinite(Number(item.amount))
    )) throw new Error("invalid");
    if (transactions.value.length && !window.confirm("Die vorhandene Historie durch den Import ersetzen?")) return;
    transactions.value = imported;
    emit("notice", "Historie importiert");
  } catch {
    emit("notice", "Diese Datei enthält keine gültige Historie");
  } finally {
    event.target.value = "";
  }
}
</script>

<template>
  <section class="balance-page">
    <div class="balance-hero">
      <p class="section-label">Kartenguthaben</p>
      <strong :class="{ negative: balance < 0 }">{{ formatMoney(balance) }}</strong>
      <span>nur auf diesem Gerät gespeichert</span>
    </div>

    <div class="tracker-grid">
      <form class="tracker-card" @submit.prevent="addDeposit">
        <h2>Geld einzahlen</h2>
        <label>
          Betrag
          <input v-model="depositAmount" inputmode="decimal" placeholder="z. B. 25,00" required>
        </label>
        <button type="submit" class="primary-button">Einzahlung speichern</button>
      </form>

      <form class="tracker-card" @submit.prevent="addMeal">
        <h2>Menü abbuchen</h2>
        <label>
          Tag
          <select v-model="mealDate" required>
            <option v-for="date in dates" :key="date" :value="date">
              {{ menuData.tage[date].wochentag }}, {{ formatDate(date) }}
            </option>
          </select>
        </label>
        <label>
          Gegessenes Menü
          <select v-model="selectedMealIndex" required>
            <option value="" disabled>Bitte auswählen</option>
            <option v-for="(meal, index) in mealsForDate" :key="meal['menü']" :value="index">
              {{ meal["menü"] }} · {{ meal.gericht }} · {{ formatMoney(meal.preis_intern_eur) }}
            </option>
          </select>
        </label>
        <button type="submit" class="primary-button" :disabled="!selectedMeal">Internen Preis abbuchen</button>
      </form>

      <form class="tracker-card" @submit.prevent="addExpense">
        <h2>Manuelle Ausgabe</h2>
        <div class="field-row">
          <label>
            Betrag
            <input v-model="expenseAmount" inputmode="decimal" placeholder="z. B. 3,50" required>
          </label>
          <label>
            Datum
            <input v-model="expenseDate" type="date" required>
          </label>
        </div>
        <label>
          Beschreibung <span class="optional">optional</span>
          <input v-model="expenseDescription" placeholder="z. B. Kaffee und Nachtisch">
        </label>
        <button type="submit" class="primary-button">Ausgabe speichern</button>
      </form>
    </div>

    <section class="history-section">
      <div class="history-heading">
        <div>
          <p class="section-label">Verlauf</p>
          <h2>Buchungshistorie</h2>
        </div>
        <div class="history-tools">
          <button type="button" class="secondary-button" @click="exportTransactions">Exportieren</button>
          <button type="button" class="secondary-button" @click="importInput?.click()">Importieren</button>
          <input ref="importInput" class="visually-hidden" type="file" accept="application/json" @change="importTransactions">
        </div>
      </div>

      <p v-if="!sortedTransactions.length" class="state-card">Noch keine Buchungen gespeichert.</p>
      <ul v-else class="transaction-list">
        <li v-for="item in sortedTransactions" :key="item.id">
          <div>
            <strong>{{ transactionTitle(item) }}</strong>
            <span>{{ formatDate(item.date) }}</span>
          </div>
          <span class="transaction-amount" :class="{ income: item.amount > 0 }">
            {{ item.amount > 0 ? "+" : "" }}{{ formatMoney(item.amount) }}
          </span>
          <button type="button" class="delete-button" aria-label="Buchung löschen" @click="removeTransaction(item.id)">×</button>
        </li>
      </ul>
    </section>
  </section>
</template>
