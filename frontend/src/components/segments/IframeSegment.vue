<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <iframe
    :src="segment.content"
    :title="segment.title"
    class="h-[600px] w-full rounded border-none"
    sandbox="allow-scripts allow-same-origin allow-popups"
    allow="fullscreen"
  />
</template>
