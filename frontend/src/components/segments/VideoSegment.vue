<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <video
    :src="segment.content"
    controls
    class="w-full rounded"
  >
    Your browser does not support the video element.
  </video>
</template>
