<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <iframe
    :src="segment.content"
    class="h-[85vh] w-full rounded border-none"
    :title="segment.title"
  />
</template>
