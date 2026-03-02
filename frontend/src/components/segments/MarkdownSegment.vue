<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";
import type { Segment } from "@/types/segment";

const props = defineProps<{
  segment: Segment;
}>();

const html = computed(() => marked.parse(props.segment.content) as string);
</script>

<template>
  <div class="prose max-w-none dark:prose-invert" v-html="html" />
</template>
