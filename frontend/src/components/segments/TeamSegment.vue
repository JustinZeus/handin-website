<script setup lang="ts">
import { computed } from "vue";
import type { Segment } from "@/types/segment";

const props = defineProps<{
  segment: Segment;
}>();

interface TeamMember {
  name: string;
  student_number: string;
}

const members = computed<TeamMember[]>(() => {
  const raw = props.segment.metadata.members;
  return Array.isArray(raw) ? (raw as TeamMember[]) : [];
});
</script>

<template>
  <ul class="divide-y divide-slate-200 dark:divide-slate-700">
    <li
      v-for="(member, i) in members"
      :key="i"
      class="flex items-center justify-between py-2 text-sm"
    >
      <span class="font-medium text-slate-900 dark:text-slate-100">{{ member.name }}</span>
      <span class="font-mono text-slate-500 dark:text-slate-400">{{ member.student_number }}</span>
    </li>
  </ul>
</template>
