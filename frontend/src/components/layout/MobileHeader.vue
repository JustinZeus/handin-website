<script setup lang="ts">
import { ref } from "vue";
import type { Segment } from "@/types/segment";

defineProps<{
  siteTitle: string;
  segments: Segment[];
  activeId: string | null;
}>();

const emit = defineEmits<{
  navigate: [id: string];
}>();

const open = ref(false);

function toggle() {
  open.value = !open.value;
}

function handleNav(id: string) {
  open.value = false;
  emit("navigate", id);
}

function handleBackdropClick() {
  open.value = false;
}
</script>

<template>
  <!-- Mobile nav bar -->
  <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5 dark:border-slate-700 dark:bg-slate-800">
    <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Sections</span>
    <button
      class="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
      aria-label="Open navigation"
      @click="toggle"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  </div>

  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="open"
      class="fixed inset-0 z-40 bg-black/40"
      @click="handleBackdropClick"
    />
  </Transition>

  <!-- Dropdown panel -->
  <Transition name="dropdown">
    <div
      v-if="open"
      class="fixed top-0 right-0 left-0 z-50"
    >
      <div class="bg-white shadow-lg dark:bg-slate-800">
        <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
          <span class="text-sm font-semibold text-slate-900 dark:text-slate-100">{{ siteTitle }}</span>
          <button
            class="text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            aria-label="Close navigation"
            @click="toggle"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <ul class="max-h-80 overflow-y-auto py-1">
          <li v-for="segment in segments" :key="segment.id">
            <!-- External link segments -->
            <a
              v-if="segment.type === 'link'"
              :href="segment.content"
              target="_blank"
              rel="noopener noreferrer"
              class="flex w-full items-center gap-1 px-4 py-2.5 text-left text-sm text-slate-600 transition-colors duration-150 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100"
              @click="open = false"
            >
              {{ segment.title }}
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
            <!-- Regular segment nav buttons -->
            <button
              v-else
              class="w-full px-4 py-2.5 text-left text-sm transition-colors duration-150"
              :class="
                activeId === segment.id
                  ? 'bg-primary-50 font-medium text-slate-900 dark:bg-primary-700/20 dark:text-slate-100'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100'
              "
              @click="handleNav(segment.id)"
            >
              {{ segment.title }}
            </button>
          </li>
        </ul>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: transform 200ms ease, opacity 200ms ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
