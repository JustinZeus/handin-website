<script setup lang="ts">
defineEmits<{
  "add-segment": [];
  logout: [];
}>();
</script>

<template>
  <div class="border-b border-primary-100 bg-primary-50 px-6 py-2 dark:border-primary-700/30 dark:bg-slate-800">
    <div class="mx-auto flex max-w-6xl items-center justify-between">
      <span class="rounded bg-primary-200 px-2 py-0.5 text-xs font-semibold text-primary-700 dark:bg-primary-700/30 dark:text-primary-300">
        Editing
      </span>
      <div class="flex items-center gap-3">
        <button
          class="rounded bg-primary-300 px-3 py-1.5 text-sm font-medium text-slate-900 transition-colors hover:bg-primary-400 dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500"
          @click="$emit('add-segment')"
        >
          + Add Segment
        </button>
        <button
          class="rounded px-3 py-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          @click="$emit('logout')"
        >
          Logout
        </button>
      </div>
    </div>
  </div>
</template>
