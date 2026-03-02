<script setup lang="ts">
import { ref, computed } from "vue";
import type { SegmentType } from "@/types/segment";
import AssetUploader from "@/components/admin/AssetUploader.vue";

const emit = defineEmits<{
  create: [data: { type: SegmentType; title: string; content: string; metadata?: Record<string, unknown> }];
  cancel: [];
}>();

const segmentTypes: { value: SegmentType; label: string }[] = [
  { value: "markdown", label: "Markdown" },
  { value: "pdf", label: "PDF" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
  { value: "iframe", label: "Iframe" },
  { value: "gallery", label: "Gallery" },
  { value: "link", label: "Link" },
];

const selectedType = ref<SegmentType>("markdown");
const title = ref("");
const content = ref("");
const galleryImages = ref<string[]>([]);

const canSubmit = computed(() => {
  if (!title.value.trim()) return false;
  if (selectedType.value === "gallery") return galleryImages.value.length > 0;
  if (selectedType.value === "markdown") return true;
  return content.value.trim().length > 0;
});

function handleAssetUploaded(filename: string) {
  content.value = `/api/assets/${filename}`;
}

function handleGalleryImageUploaded(filename: string) {
  galleryImages.value = [...galleryImages.value, `/api/assets/${filename}`];
}

function removeGalleryImage(index: number) {
  galleryImages.value = galleryImages.value.filter((_, i) => i !== index);
}

function handleSubmit() {
  const data: { type: SegmentType; title: string; content: string; metadata?: Record<string, unknown> } = {
    type: selectedType.value,
    title: title.value.trim(),
    content: content.value,
  };
  if (selectedType.value === "gallery") {
    data.metadata = { images: galleryImages.value };
  }
  emit("create", data);
}

const assetAcceptMap: Record<string, string> = {
  pdf: "application/pdf",
  video: "video/*",
  audio: "audio/*",
};
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="$emit('cancel')"
    >
      <div class="mx-4 w-full max-w-lg rounded-lg bg-white p-6 shadow-xl dark:bg-slate-800">
        <h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Add New Segment</h2>

        <!-- Type selector: button group -->
        <div class="mb-4">
          <label class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">Type</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="st in segmentTypes"
              :key="st.value"
              class="rounded-full px-3 py-1 text-sm font-medium transition-colors"
              :class="
                selectedType === st.value
                  ? 'bg-primary-300 text-slate-900 dark:bg-primary-600 dark:text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
              "
              @click="selectedType = st.value; content = ''; galleryImages = []"
            >
              {{ st.label }}
            </button>
          </div>
        </div>

        <!-- Title -->
        <div class="mb-4">
          <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Title</label>
          <input
            v-model="title"
            type="text"
            placeholder="Segment title"
            class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
        </div>

        <!-- Content: type-dependent -->
        <div class="mb-4">
          <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Content</label>

          <!-- Markdown: textarea -->
          <textarea
            v-if="selectedType === 'markdown'"
            v-model="content"
            rows="6"
            placeholder="Markdown content..."
            class="w-full rounded border border-slate-300 px-3 py-2 font-mono text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />

          <!-- Iframe / Link: URL input -->
          <input
            v-else-if="selectedType === 'iframe' || selectedType === 'link'"
            v-model="content"
            type="url"
            :placeholder="selectedType === 'link' ? 'https://external-site.com' : 'https://...'"
            class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />

          <!-- PDF / Video / Audio -->
          <div v-else-if="selectedType === 'pdf' || selectedType === 'video' || selectedType === 'audio'">
            <div v-if="content" class="mb-2 flex items-center gap-2 rounded bg-slate-50 px-3 py-2 text-sm text-slate-600">
              <span class="truncate">{{ content }}</span>
              <button class="shrink-0 text-red-400 hover:text-red-600" @click="content = ''">&times;</button>
            </div>
            <AssetUploader
              :accept="assetAcceptMap[selectedType]"
              :label="`Upload ${selectedType} file`"
              @uploaded="handleAssetUploaded"
            />
          </div>

          <!-- Gallery -->
          <div v-else-if="selectedType === 'gallery'">
            <div v-if="galleryImages.length > 0" class="mb-3 grid grid-cols-4 gap-2">
              <div
                v-for="(img, i) in galleryImages"
                :key="i"
                class="group relative aspect-square overflow-hidden rounded bg-slate-100"
              >
                <img :src="img" class="h-full w-full object-cover" />
                <button
                  class="absolute right-1 top-1 hidden rounded bg-red-500 px-1.5 text-xs text-white group-hover:block"
                  @click="removeGalleryImage(i)"
                >
                  &times;
                </button>
              </div>
            </div>
            <AssetUploader accept="image/*" label="Upload gallery image" @uploaded="handleGalleryImageUploaded" />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-2">
          <button
            class="rounded px-3 py-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            @click="$emit('cancel')"
          >
            Cancel
          </button>
          <button
            :disabled="!canSubmit"
            class="rounded bg-primary-300 px-4 py-1.5 text-sm font-medium text-slate-900 transition-colors hover:bg-primary-400 disabled:opacity-50 dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500"
            @click="handleSubmit"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
