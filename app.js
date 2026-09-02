const DATA_URL = "data/speiseplan.json";
const dayPicker = document.querySelector("#day-picker");
const menuList = document.querySelector("#menu-list");
const weekRange = document.querySelector("#week-range");
const template = document.querySelector("#menu-card-template");
const toast = document.querySelector("#toast");

const dateFormatter = new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit" });
const rangeFormatter = new Intl.DateTimeFormat("de-DE", { day: "numeric", month: "long", year: "numeric" });

let menuData;
let toastTimer;

function localDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseDate(key) {
  return new Date(`${key}T12:00:00`);
}

function formatNumber(value) {
  return new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 }).format(value);
}

function showToast(message) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("visible");
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2200);
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const area = document.createElement("textarea");
  area.value = text;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  document.execCommand("copy");
  area.remove();
}

function dietLabel(item) {
  if (item.ernaehrungsform === "fleisch/fisch") return "Fleisch / Fisch";
  if (item.ernaehrungsform === "vegetarisch") return "Vegetarisch";
  if (item.ernaehrungsform === "vegan") return "Vegan";
  return "Nicht zugeordnet";
}

function renderMenu(dateKey) {
  const day = menuData.tage[dateKey];
  if (!day) return;

  document.querySelectorAll(".day-button").forEach((button) => {
    const active = button.dataset.date === dateKey;
    button.classList.toggle("active", active);
    button.setAttribute("aria-current", active ? "date" : "false");
  });

  menuList.replaceChildren();
  day.gerichte.forEach((item) => {
    const card = template.content.firstElementChild.cloneNode(true);
    const badge = card.querySelector(".diet-badge");
    const calories = card.querySelector(".calories");
    const proteinTypes = card.querySelector(".protein-types");
    const copyButton = card.querySelector(".copy-button");
    let portion = 1;

    card.querySelector(".menu-name").textContent = item["menü"];
    card.querySelector(".dish-name").textContent = item.gericht;
    card.querySelector(".description").textContent = item.beschreibung.replaceAll(" / ", " · ");
    badge.textContent = dietLabel(item);
    badge.classList.add(item.ernaehrungsform.replace("/", "-"));
    proteinTypes.textContent = item.proteintypen?.length
      ? item.proteintypen.map((word) => word[0].toUpperCase() + word.slice(1)).join(" + ")
      : "";

    function updateCalories() {
      calories.textContent = `ca. ${formatNumber(item.kcal * portion)} kcal`;
    }
    updateCalories();

    card.querySelectorAll("[data-portion]").forEach((button) => {
      button.addEventListener("click", () => {
        portion = Number(button.dataset.portion);
        card.querySelectorAll("[data-portion]").forEach((candidate) => {
          candidate.classList.toggle("active", candidate === button);
        });
        updateCalories();
      });
    });

    copyButton.addEventListener("click", async () => {
      const kcal = Math.round(item.kcal * portion);
      const portionText = portion === 0.5 ? "Halbe Portion" : portion === 1.5 ? "Anderthalbfache Portion" : "Eine Portion";
      const text = `${item.beschreibung}. ${portionText} laut UKE-Casino ca. ${kcal} kcal.`;
      try {
        await copyText(text);
        showToast("Für YAZIO kopiert");
      } catch {
        showToast("Kopieren nicht möglich");
      }
    });

    menuList.append(card);
  });
}

function renderDayPicker() {
  const dates = Object.keys(menuData.tage);
  dates.forEach((dateKey) => {
    const day = menuData.tage[dateKey];
    const button = document.createElement("button");
    button.type = "button";
    button.className = "day-button";
    button.dataset.date = dateKey;
    button.innerHTML = `<span class="day-short">${day.wochentag.slice(0, 2)}</span><span class="day-number">${dateFormatter.format(parseDate(dateKey))}</span>`;
    button.addEventListener("click", () => renderMenu(dateKey));
    dayPicker.append(button);
  });

  const today = localDateKey();
  renderMenu(menuData.tage[today] ? today : dates[0]);
}

async function init() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    menuData = await response.json();
    weekRange.textContent = `${rangeFormatter.format(parseDate(menuData.zeitraum_von))} – ${rangeFormatter.format(parseDate(menuData.zeitraum_bis))}`;
    renderDayPicker();
  } catch (error) {
    console.error(error);
    menuList.innerHTML = '<p class="state-message">Der Speiseplan konnte nicht geladen werden.</p>';
  }
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("service-worker.js"));
}

init();
