<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import type { Segment } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";
import { useDarkMode } from "@/composables/useDarkMode";
import SidebarNav from "@/components/layout/SidebarNav.vue";
import MobileHeader from "@/components/layout/MobileHeader.vue";
import TokenPrompt from "@/components/admin/TokenPrompt.vue";
import AdminToolbar from "@/components/admin/AdminToolbar.vue";

defineProps<{
  segments: Segment[];
  siteTitle: string;
  activeId: string | null;
}>();

const emit = defineEmits<{
  navigate: [id: string];
  "add-segment": [];
  logout: [];
}>();

const { isAdmin } = useAdmin();
const { isDark, toggle: toggleDark } = useDarkMode();

const showBackToTop = ref(false);

function handleScroll() {
  showBackToTop.value = window.scrollY > 300;
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function handleNavigate(id: string) {
  emit("navigate", id);
}

onMounted(() => {
  window.addEventListener("scroll", handleScroll, { passive: true });
});

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
});
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900">
    <!-- Sticky header: title bar + nav -->
    <div class="sticky top-0 z-20">
      <!-- Title bar -->
      <header class="flex items-center justify-between bg-primary-300 px-6 py-4">
        <h1 class="text-xl font-bold text-slate-900">{{ siteTitle }}</h1>
        <div class="flex items-center gap-2">
          <!-- Dark mode toggle -->
          <button
            class="rounded p-1.5 text-slate-700 transition-colors hover:bg-primary-400/30"
            :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            @click="toggleDark"
          >
            <!-- Sun icon (shown in dark mode) -->
            <svg v-if="isDark" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <!-- Moon icon (shown in light mode) -->
            <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
          <TokenPrompt />
        </div>
      </header>

      <!-- Desktop tab nav -->
      <div class="hidden md:block">
        <SidebarNav
          :segments="segments"
          :site-title="siteTitle"
          :active-id="activeId"
          @navigate="handleNavigate"
        />
      </div>

      <!-- Mobile header with hamburger -->
      <div class="md:hidden">
        <MobileHeader
          :site-title="siteTitle"
          :segments="segments"
          :active-id="activeId"
          @navigate="handleNavigate"
        />
      </div>
    </div>

    <!-- Admin toolbar -->
    <AdminToolbar
      v-if="isAdmin"
      @add-segment="$emit('add-segment')"
      @logout="$emit('logout')"
    />

    <!-- Main content -->
    <main class="mx-auto max-w-6xl px-6 py-8">
      <slot />
    </main>

    <!-- Back to top button -->
    <Transition name="fade-up">
      <button
        v-if="showBackToTop"
        class="fixed right-6 bottom-6 z-30 rounded-full bg-primary-300 p-3 shadow-lg transition-colors hover:bg-primary-400"
        title="Back to top"
        @click="scrollToTop"
      >
        <svg class="h-5 w-5 text-slate-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
