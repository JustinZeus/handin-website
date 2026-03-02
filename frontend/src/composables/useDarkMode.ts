import { ref, watch } from "vue";

const isDark = ref(false);

// Initialize from localStorage or system preference
const stored = localStorage.getItem("dark_mode");
if (stored !== null) {
  isDark.value = stored === "true";
} else {
  isDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
}

// Apply class to <html>
function applyClass() {
  document.documentElement.classList.toggle("dark", isDark.value);
}
applyClass();

watch(isDark, () => {
  applyClass();
  localStorage.setItem("dark_mode", String(isDark.value));
});

export function useDarkMode() {
  function toggle() {
    isDark.value = !isDark.value;
  }

  return { isDark, toggle };
}
