<script setup lang="ts">
import { ref } from "vue";
import { useAdmin } from "@/composables/useAdmin";
import { useAssetUpload } from "@/composables/useAssetUpload";

const props = defineProps<{
  accept?: string;
  label?: string;
}>();

const emit = defineEmits<{
  uploaded: [filename: string];
}>();

const { authHeaders } = useAdmin();
const { uploading, error, upload } = useAssetUpload();
const dragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

async function handleFile(file: File) {
  const filename = await upload(file, authHeaders.value);
  if (filename) {
    emit("uploaded", filename);
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  const file = e.dataTransfer?.files[0];
  if (file) void handleFile(file);
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) void handleFile(file);
  target.value = "";
}
</script>

<template>
  <div
    class="relative cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-colors"
    :class="dragging ? 'border-primary-300 bg-primary-50 dark:border-primary-500 dark:bg-primary-900/20' : 'border-slate-300 hover:border-primary-300 dark:border-slate-600 dark:hover:border-primary-500'"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="fileInput?.click()"
  >
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      :accept="props.accept"
      @change="onFileSelect"
    />

    <div v-if="uploading" class="text-sm text-slate-500 dark:text-slate-400">Uploading...</div>
    <div v-else>
      <svg class="mx-auto mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <p class="text-sm text-slate-500 dark:text-slate-400">{{ props.label ?? "Drop file here or click to browse" }}</p>
    </div>

    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>
  </div>
</template>
