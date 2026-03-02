<script setup lang="ts">
import { computed } from "vue";
import type { Segment } from "@/types/segment";

const props = defineProps<{
  segment: Segment;
}>();

const images = computed(() => {
  const meta = props.segment.metadata;
  if (Array.isArray(meta.images)) {
    return meta.images as string[];
  }
  return [];
});
</script>

<template>
  <div class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
    <img
      v-for="(src, index) in images"
      :key="index"
      :src="src"
      :alt="`${segment.title} image ${index + 1}`"
      class="aspect-square w-full rounded object-cover"
    />
  </div>
</template>
