<script setup lang="ts">
import { ref, computed } from "vue";
import type { SegmentType, Source } from "@/types/segment";
import AssetUploader from "@/components/admin/AssetUploader.vue";
import RichTextEditor from "@/components/admin/RichTextEditor.vue";
import { formatApaCitation } from "@/utils/formatApa";

const emit = defineEmits<{
  create: [data: { type: SegmentType; title: string; content: string; metadata?: Record<string, unknown> }];
  cancel: [];
}>();

const segmentTypes: { value: SegmentType; label: string; description: string; icon: string }[] = [
  { value: "markdown", label: "Text", description: "Write formatted text, headings, and lists", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h10M4 18h6" /></svg>' },
  { value: "gallery", label: "Images", description: "Display a photo gallery", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /><circle cx="8.5" cy="8.5" r="1.5" stroke-width="2" /><polyline points="21 15 16 10 5 21" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>' },
  { value: "pdf", label: "PDF", description: "Show a PDF document", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { value: "video", label: "Video", description: "Embed a video file", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>' },
  { value: "audio", label: "Audio", description: "Embed an audio file", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072M12 6v12m0 0a3 3 0 003-3V9a3 3 0 00-3 3m0 0a3 3 0 01-3 3V9a3 3 0 013-3" /></svg>' },
  { value: "iframe", label: "Embed", description: "Embed an external website or tool", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>' },
  { value: "sources", label: "Sources", description: "Add an APA reference list", icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>' },
];

const selectedType = ref<SegmentType>("markdown");
const title = ref("");
const content = ref("");
const galleryImages = ref<string[]>([]);
const sources = ref<Source[]>([]);
const sourceForm = ref({ authors: "", year: "", title: "", source: "", url: "" });

function addSource() {
  const f = sourceForm.value;
  if (!f.authors.trim() && !f.title.trim()) return;
  sources.value = [...sources.value, { id: crypto.randomUUID(), ...f }];
  sourceForm.value = { authors: "", year: "", title: "", source: "", url: "" };
}

function removeSource(id: string) {
  sources.value = sources.value.filter((s) => s.id !== id);
}

const canSubmit = computed(() => {
  if (selectedType.value === "gallery") return galleryImages.value.length > 0;
  if (selectedType.value === "sources") return sources.value.length > 0;
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
  if (selectedType.value === "sources") {
    data.metadata = { sources: sources.value };
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
      <div class="mx-4 w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Add a new section</h2>

        <!-- Type selector: icon cards -->
        <div class="mb-5">
          <div class="grid grid-cols-3 gap-2 sm:grid-cols-7">
            <button
              v-for="st in segmentTypes"
              :key="st.value"
              type="button"
              class="flex flex-col items-center gap-1.5 rounded-lg border-2 py-3 px-2 transition-colors"
              :class="
                selectedType === st.value
                  ? 'border-primary-300 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
              "
              :title="st.description"
              @click="selectedType = st.value; content = ''; galleryImages = []; sources = []"
            >
              <span class="text-gray-500 dark:text-gray-400" v-html="st.icon" />
              <span class="text-xs font-medium text-gray-900 dark:text-gray-100">{{ st.label }}</span>
            </button>
          </div>
        </div>

        <!-- Title -->
        <div class="mb-4">
          <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Section title <span class="font-normal text-gray-400">(optional)</span>
          </label>
          <input
            v-model="title"
            type="text"
            placeholder="Give this section a title"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
          />
        </div>

        <!-- Content: type-dependent -->
        <div class="mb-5">
          <label class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Content</label>

          <!-- Markdown: rich text editor -->
          <RichTextEditor v-if="selectedType === 'markdown'" v-model="content" />

          <!-- Iframe: URL input -->
          <div v-else-if="selectedType === 'iframe'">
            <p class="mb-2 text-xs text-gray-400">Paste the URL of the website or tool you want to embed.</p>
            <input
              v-model="content"
              type="url"
              placeholder="https://..."
              class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
            />
          </div>

          <!-- PDF / Video / Audio -->
          <div v-else-if="selectedType === 'pdf' || selectedType === 'video' || selectedType === 'audio'">
            <div v-if="content" class="mb-2 flex items-center gap-2 rounded bg-gray-50 px-3 py-2 text-sm text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              <span class="truncate">{{ content }}</span>
              <button class="shrink-0 text-red-400 hover:text-red-600" @click="content = ''">&times;</button>
            </div>
            <AssetUploader
              :accept="assetAcceptMap[selectedType]"
              :label="`Click to upload your ${selectedType} file, or drag and drop`"
              @uploaded="handleAssetUploaded"
            />
          </div>

          <!-- Gallery -->
          <div v-else-if="selectedType === 'gallery'">
            <p class="mb-2 text-xs text-gray-400">Upload one or more photos. You can add more later.</p>
            <div v-if="galleryImages.length > 0" class="mb-3 grid grid-cols-4 gap-2">
              <div
                v-for="(img, i) in galleryImages"
                :key="i"
                class="group relative aspect-square overflow-hidden rounded bg-gray-100 dark:bg-gray-700"
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
            <AssetUploader accept="image/*" :multiple="true" label="Click to upload photos, or drag and drop" @uploaded="handleGalleryImageUploaded" />
          </div>

          <!-- Sources -->
          <div v-else-if="selectedType === 'sources'">
            <!-- Added sources list -->
            <div v-if="sources.length > 0" class="mb-3 space-y-2">
              <div
                v-for="source in sources"
                :key="source.id"
                class="group flex items-start gap-2 rounded bg-gray-50 px-3 py-2 text-sm dark:bg-gray-700"
              >
                <p
                  class="min-w-0 flex-1 pl-6 -indent-6 text-gray-700 dark:text-gray-200"
                  v-html="formatApaCitation(source)"
                />
                <button
                  class="shrink-0 text-red-400 hover:text-red-600"
                  @click="removeSource(source.id)"
                >
                  &times;
                </button>
              </div>
            </div>

            <!-- Source input form -->
            <div class="space-y-2">
              <div class="flex gap-2">
                <input
                  v-model="sourceForm.authors"
                  type="text"
                  placeholder="Authors (e.g. Liu, Z., Zhang, W., & Yang, P.)"
                  class="min-w-0 flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
                />
                <input
                  v-model="sourceForm.year"
                  type="text"
                  placeholder="Year"
                  class="w-20 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
                />
              </div>
              <input
                v-model="sourceForm.title"
                type="text"
                placeholder="Title"
                class="w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
              />
              <div class="flex gap-2">
                <input
                  v-model="sourceForm.source"
                  type="text"
                  placeholder="Journal, publisher, or site name"
                  class="min-w-0 flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
                />
                <input
                  v-model="sourceForm.url"
                  type="text"
                  placeholder="URL or DOI link (optional)"
                  class="min-w-0 flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
                />
              </div>
              <button
                :disabled="!sourceForm.authors.trim() && !sourceForm.title.trim()"
                class="rounded bg-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-300 disabled:opacity-50 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
                @click="addSource"
              >
                Add source
              </button>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-2">
          <button
            class="rounded px-3 py-1.5 text-sm text-gray-500 transition-colors hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            @click="$emit('cancel')"
          >
            Cancel
          </button>
          <button
            :disabled="!canSubmit"
            class="rounded bg-primary-300 px-4 py-1.5 text-sm font-medium text-gray-900 transition-colors hover:bg-primary-400 disabled:opacity-50"
            @click="handleSubmit"
          >
            Add section
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
