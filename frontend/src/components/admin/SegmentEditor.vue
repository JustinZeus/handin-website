<script setup lang="ts">
import { ref } from "vue";
import type { Segment } from "@/types/segment";
import AssetUploader from "@/components/admin/AssetUploader.vue";

const props = defineProps<{
  segment: Segment;
}>();

const emit = defineEmits<{
  save: [updates: { title?: string; content?: string; metadata?: Record<string, unknown> }];
  cancel: [];
  delete: [];
}>();

const title = ref(props.segment.title);
const content = ref(props.segment.content);
const metadata = ref<Record<string, unknown>>({ ...props.segment.metadata });
const showDeleteConfirm = ref(false);

function handleSave() {
  const updates: { title?: string; content?: string; metadata?: Record<string, unknown> } = {};
  if (title.value !== props.segment.title) updates.title = title.value;
  if (content.value !== props.segment.content) updates.content = content.value;
  if (JSON.stringify(metadata.value) !== JSON.stringify(props.segment.metadata)) {
    updates.metadata = metadata.value;
  }
  emit("save", updates);
}

function handleAssetUploaded(filename: string) {
  content.value = `/api/assets/${filename}`;
}

function handleGalleryImageUploaded(filename: string) {
  const images = Array.isArray(metadata.value.images)
    ? [...(metadata.value.images as string[])]
    : [];
  images.push(`/api/assets/${filename}`);
  metadata.value = { ...metadata.value, images };
}

function removeGalleryImage(index: number) {
  const images = Array.isArray(metadata.value.images)
    ? [...(metadata.value.images as string[])]
    : [];
  images.splice(index, 1);
  metadata.value = { ...metadata.value, images };
}

const assetAcceptMap: Record<string, string> = {
  pdf: "application/pdf",
  video: "video/*",
  audio: "audio/*",
};
</script>

<template>
  <div class="mt-4 rounded-lg border border-primary-100 bg-primary-50/50 p-4 dark:border-slate-600 dark:bg-slate-700/50">
    <!-- Title -->
    <div class="mb-4">
      <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Title</label>
      <input
        v-model="title"
        type="text"
        class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
      />
    </div>

    <!-- Content: depends on segment type -->
    <div class="mb-4">
      <label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Content</label>

      <!-- Markdown: textarea -->
      <textarea
        v-if="segment.type === 'markdown'"
        v-model="content"
        rows="8"
        class="w-full rounded border border-slate-300 px-3 py-2 font-mono text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
      />

      <!-- Iframe / Link: URL input -->
      <input
        v-else-if="segment.type === 'iframe' || segment.type === 'link'"
        v-model="content"
        type="url"
        :placeholder="segment.type === 'link' ? 'https://external-site.com' : 'https://...'"
        class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
      />

      <!-- PDF / Video / Audio: file upload + URL display -->
      <div v-else-if="segment.type === 'pdf' || segment.type === 'video' || segment.type === 'audio'">
        <div v-if="content" class="mb-2 flex items-center gap-2 rounded bg-white px-3 py-2 text-sm text-slate-600 dark:bg-slate-700 dark:text-slate-300">
          <span class="truncate">{{ content }}</span>
          <button
            class="shrink-0 text-red-400 hover:text-red-600"
            @click="content = ''"
          >
            &times;
          </button>
        </div>
        <AssetUploader
          :accept="assetAcceptMap[segment.type]"
          :label="`Upload ${segment.type} file`"
          @uploaded="handleAssetUploaded"
        />
      </div>

      <!-- Gallery: multiple image upload -->
      <div v-else-if="segment.type === 'gallery'">
        <div v-if="Array.isArray(metadata.images) && (metadata.images as string[]).length > 0" class="mb-3 grid grid-cols-4 gap-2">
          <div
            v-for="(img, i) in (metadata.images as string[])"
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
        <AssetUploader
          accept="image/*"
          label="Upload gallery image"
          @uploaded="handleGalleryImageUploaded"
        />
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between">
      <button
        class="rounded px-3 py-1.5 text-sm text-red-500 transition-colors hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/30"
        @click="showDeleteConfirm = true"
      >
        Delete
      </button>
      <div class="flex gap-2">
        <button
          class="rounded px-3 py-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          @click="$emit('cancel')"
        >
          Cancel
        </button>
        <button
          class="rounded bg-primary-300 px-4 py-1.5 text-sm font-medium text-slate-900 transition-colors hover:bg-primary-400 dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500"
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        @click.self="showDeleteConfirm = false"
      >
        <div class="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl dark:bg-slate-800">
          <h3 class="mb-2 text-lg font-semibold text-slate-900 dark:text-slate-100">Delete Segment</h3>
          <p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
            Are you sure you want to delete <strong>"{{ segment.title }}"</strong>? This action cannot be undone.
          </p>
          <div class="flex justify-end gap-2">
            <button
              class="rounded px-3 py-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              @click="showDeleteConfirm = false"
            >
              Cancel
            </button>
            <button
              class="rounded bg-red-500 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
              @click="showDeleteConfirm = false; $emit('delete')"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
