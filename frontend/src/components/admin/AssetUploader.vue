<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useAdmin } from "@/composables/useAdmin";
import { useAssetUpload } from "@/composables/useAssetUpload";

const props = defineProps<{
  accept?: string;
  label?: string;
  multiple?: boolean;
}>();

const emit = defineEmits<{
  uploaded: [filename: string];
}>();

const { authHeaders } = useAdmin();
const { upload } = useAssetUpload();
const dragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

// Track batch upload state independently of the per-request composable
const busy = ref(false);
const progressLabel = ref("");
const uploadError = ref<string | null>(null);

// Ensure the `multiple` HTML attribute is set directly on the DOM node,
// since some GTK/GNOME file pickers only respect the attribute, not the
// DOM property that Vue's :multiple binding sets.
function applyMultiple() {
  if (!fileInput.value) return;
  if (props.multiple) {
    fileInput.value.setAttribute("multiple", "");
  } else {
    fileInput.value.removeAttribute("multiple");
  }
}

onMounted(applyMultiple);
watch(() => props.multiple, applyMultiple);

async function handleFiles(files: File[]) {
  if (files.length === 0) return;
  busy.value = true;
  uploadError.value = null;
  try {
    for (let i = 0; i < files.length; i++) {
      progressLabel.value = files.length > 1
        ? `Uploading ${i + 1} of ${files.length}…`
        : "Uploading…";
      const filename = await upload(files[i], authHeaders.value);
      if (filename) {
        emit("uploaded", filename);
      }
    }
  } finally {
    busy.value = false;
    progressLabel.value = "";
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  const files = Array.from(e.dataTransfer?.files ?? []);
  void handleFiles(files);
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  const files = Array.from(target.files ?? []);
  target.value = "";
  void handleFiles(files);
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
    <!-- Hidden file input: multiple attribute set imperatively via onMounted/watch -->
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      :accept="props.accept"
      @click.stop
      @change="onFileSelect"
    />

    <div v-if="busy" class="text-sm text-slate-500 dark:text-slate-400">
      {{ progressLabel }}
    </div>
    <div v-else>
      <svg class="mx-auto mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <p class="text-sm text-slate-500 dark:text-slate-400">{{ props.label ?? "Drop file here or click to browse" }}</p>
    </div>

    <p v-if="uploadError" class="mt-2 text-sm text-red-500">{{ uploadError }}</p>
  </div>
</template>
