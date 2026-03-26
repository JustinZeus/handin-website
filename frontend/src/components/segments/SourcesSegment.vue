<script setup lang="ts">
import { computed } from "vue";
import type { Segment, Source } from "@/types/segment";
import { formatApaCitation } from "@/utils/formatApa";

const props = defineProps<{
  segment: Segment;
}>();

const sortedSources = computed(() => {
  const sources = Array.isArray(props.segment.metadata.sources)
    ? ([...props.segment.metadata.sources] as Source[])
    : [];
  return sources.sort((a, b) =>
    a.authors.localeCompare(b.authors, undefined, { sensitivity: "base" }),
  );
});
</script>

<template>
  <div v-if="sortedSources.length > 0" class="space-y-2">
    <p
      v-for="source in sortedSources"
      :key="source.id"
      class="pl-8 -indent-8 text-sm text-slate-800 dark:text-slate-200"
      v-html="formatApaCitation(source)"
    />
  </div>
  <p v-else class="text-sm italic text-slate-400 dark:text-slate-500">No sources added yet.</p>
</template>
