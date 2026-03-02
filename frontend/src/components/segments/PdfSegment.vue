<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <iframe
    :src="segment.content"
    class="h-[600px] w-full rounded border-none"
    :title="segment.title"
  />
</template>
