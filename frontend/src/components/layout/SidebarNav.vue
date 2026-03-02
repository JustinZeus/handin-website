<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segments: Segment[];
  siteTitle: string;
  activeId: string | null;
}>();

const emit = defineEmits<{
  navigate: [id: string];
}>();

function handleClick(id: string) {
  emit("navigate", id);
}
</script>

<template>
  <nav class="border-b border-slate-200 bg-white px-6 dark:border-slate-700 dark:bg-slate-800">
    <ul class="flex gap-1 overflow-x-auto">
      <li v-for="segment in segments" :key="segment.id">
        <!-- External link segments -->
        <a
          v-if="segment.type === 'link'"
          :href="segment.content"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 whitespace-nowrap border-b-2 border-transparent px-3 py-2.5 text-sm font-medium text-slate-500 transition-colors duration-150 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        >
          {{ segment.title }}
          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
        <!-- Regular segment nav buttons -->
        <button
          v-else
          class="whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors duration-150"
          :class="
            activeId === segment.id
              ? 'border-primary-400 text-slate-900 dark:text-slate-100'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
          "
          @click="handleClick(segment.id)"
        >
          {{ segment.title }}
        </button>
      </li>
    </ul>
  </nav>
</template>
