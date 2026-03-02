<script setup lang="ts">
import type { Segment } from "@/types/segment";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <audio
    :src="segment.content"
    controls
    class="w-full"
  >
    Your browser does not support the audio element.
  </audio>
</template>
