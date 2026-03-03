<script setup lang="ts">
import { ref, computed } from "vue";
import type { Segment } from "@/types/segment";

const props = defineProps<{
  segment: Segment;
}>();

const images = computed(() => {
  const meta = props.segment.metadata;
  if (Array.isArray(meta.images)) return meta.images as string[];
  return [];
});

const current = ref(0);

function prev() {
  current.value = (current.value - 1 + images.value.length) % images.value.length;
}

function next() {
  current.value = (current.value + 1) % images.value.length;
}
</script>

<template>
  <div v-if="images.length > 0" class="select-none">
    <!-- Fixed-height image box with arrows overlaid inside it -->
    <div class="relative flex h-[70vh] items-center justify-center overflow-hidden rounded bg-white dark:bg-gray-900">
      <img
        :src="images[current]"
        :alt="`${segment.title} image ${current + 1}`"
        class="h-full w-full object-contain"
      />

      <!-- Arrows (only when multiple images) -->
      <template v-if="images.length > 1">
        <button
          type="button"
          class="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-1.5 text-white transition-colors hover:bg-black/65"
          aria-label="Previous image"
          @click="prev"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button
          type="button"
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-1.5 text-white transition-colors hover:bg-black/65"
          aria-label="Next image"
          @click="next"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </template>
    </div>

    <!-- Dot indicators below (only when multiple images) -->
    <div v-if="images.length > 1" class="mt-3 flex justify-center gap-1.5">
      <button
        v-for="(_, i) in images"
        :key="i"
        type="button"
        class="h-2 rounded-full transition-all"
        :class="i === current ? 'w-4 bg-gray-600 dark:bg-gray-300' : 'w-2 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500'"
        :aria-label="`Go to image ${i + 1}`"
        @click="current = i"
      />
    </div>
  </div>
</template>
