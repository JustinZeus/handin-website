<script setup lang="ts">
import { ref } from "vue";
import type { Segment, Source } from "@/types/segment";
import AssetUploader from "@/components/admin/AssetUploader.vue";
import RichTextEditor from "@/components/admin/RichTextEditor.vue";
import { formatApaCitation } from "@/utils/formatApa";

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
const teamMembers = ref<{ name: string; student_number: string }[]>(
  Array.isArray(props.segment.metadata.members)
    ? [...(props.segment.metadata.members as { name: string; student_number: string }[])]
    : [],
);
const newMemberName = ref("");
const newMemberNumber = ref("");

const sources = ref<Source[]>(
  Array.isArray(props.segment.metadata.sources)
    ? [...(props.segment.metadata.sources as Source[])]
    : [],
);
const editingSourceId = ref<string | null>(null);
const sourceForm = ref({ authors: "", year: "", title: "", source: "", url: "" });

function resetSourceForm() {
  sourceForm.value = { authors: "", year: "", title: "", source: "", url: "" };
  editingSourceId.value = null;
}

function addOrUpdateSource() {
  const f = sourceForm.value;
  if (!f.authors.trim() && !f.title.trim()) return;
  if (editingSourceId.value) {
    sources.value = sources.value.map((s) =>
      s.id === editingSourceId.value ? { ...s, ...f } : s,
    );
  } else {
    sources.value = [...sources.value, { id: crypto.randomUUID(), ...f }];
  }
  resetSourceForm();
}

function editSource(source: Source) {
  editingSourceId.value = source.id;
  sourceForm.value = {
    authors: source.authors,
    year: source.year,
    title: source.title,
    source: source.source,
    url: source.url,
  };
}

function removeSource(id: string) {
  sources.value = sources.value.filter((s) => s.id !== id);
  if (editingSourceId.value === id) resetSourceForm();
}

function normaliseUrl(url: string): string {
  const trimmed = url.trim();
  if (trimmed && !/^https?:\/\//i.test(trimmed)) return `https://${trimmed}`;
  return trimmed;
}

function handleSave() {
  const updates: { title?: string; content?: string; metadata?: Record<string, unknown> } = {};
  if (title.value !== props.segment.title) updates.title = title.value;
  const savedContent =
    props.segment.type === "iframe" ? normaliseUrl(content.value) : content.value;
  if (savedContent !== props.segment.content) updates.content = savedContent;
  if (props.segment.type === "team") {
    metadata.value = { ...metadata.value, members: teamMembers.value };
  }
  if (props.segment.type === "sources") {
    metadata.value = { ...metadata.value, sources: sources.value };
  }
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

      <!-- Markdown: rich text editor -->
      <RichTextEditor v-if="segment.type === 'markdown'" v-model="content" />

      <!-- Iframe: URL input -->
      <div v-else-if="segment.type === 'iframe'">
        <input
          v-model="content"
          type="url"
          placeholder="https://..."
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        />
        <p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
          Most major sites (Google, GitHub, etc.) block embedding. Use dedicated embed URLs where available, e.g. YouTube's <code>youtube.com/embed/…</code>.
        </p>
      </div>

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
          :multiple="true"
          label="Click to upload photos, or drag and drop"
          @uploaded="handleGalleryImageUploaded"
        />
      </div>

      <!-- Team: member list -->
      <div v-else-if="segment.type === 'team'">
        <div v-if="teamMembers.length > 0" class="mb-3 space-y-1">
          <div
            v-for="(member, i) in teamMembers"
            :key="i"
            class="flex items-center justify-between rounded bg-white px-3 py-1.5 text-sm dark:bg-slate-700"
          >
            <span class="text-slate-900 dark:text-slate-100">{{ member.name }}</span>
            <span class="font-mono text-slate-500 dark:text-slate-400">{{ member.student_number }}</span>
            <button class="ml-2 shrink-0 text-red-400 hover:text-red-600" @click="teamMembers = teamMembers.filter((_, j) => j !== i)">&times;</button>
          </div>
        </div>
        <div class="flex gap-2">
          <input
            v-model="newMemberName"
            type="text"
            placeholder="Name"
            class="min-w-0 flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
          <input
            v-model="newMemberNumber"
            type="text"
            placeholder="Student number"
            class="w-36 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
          <button
            :disabled="!newMemberName.trim() || !newMemberNumber.trim()"
            class="rounded bg-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-300 disabled:opacity-50 dark:bg-slate-600 dark:text-slate-200 dark:hover:bg-slate-500"
            @click="teamMembers = [...teamMembers, { name: newMemberName.trim(), student_number: newMemberNumber.trim() }]; newMemberName = ''; newMemberNumber = ''"
          >
            Add
          </button>
        </div>
      </div>

      <!-- Sources: reference list -->
      <div v-else-if="segment.type === 'sources'">
        <!-- Existing sources -->
        <div v-if="sources.length > 0" class="mb-4 space-y-2">
          <div
            v-for="source in sources"
            :key="source.id"
            class="group flex items-start gap-2 rounded bg-white px-3 py-2 text-sm dark:bg-slate-700"
          >
            <p
              class="min-w-0 flex-1 pl-6 -indent-6 text-slate-700 dark:text-slate-200"
              v-html="formatApaCitation(source)"
            />
            <div class="flex shrink-0 gap-1 opacity-0 group-hover:opacity-100">
              <button
                class="rounded p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                title="Edit"
                @click="editSource(source)"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button
                class="rounded p-1 text-red-400 hover:text-red-600"
                title="Remove"
                @click="removeSource(source.id)"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <!-- Add/edit source form -->
        <div class="space-y-2">
          <div class="flex gap-2">
            <input
              v-model="sourceForm.authors"
              type="text"
              placeholder="Authors (e.g. Liu, Z., Zhang, W., & Yang, P.)"
              class="min-w-0 flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
            />
            <input
              v-model="sourceForm.year"
              type="text"
              placeholder="Year"
              class="w-20 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
            />
          </div>
          <input
            v-model="sourceForm.title"
            type="text"
            placeholder="Title"
            class="w-full rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
          />
          <div class="flex gap-2">
            <input
              v-model="sourceForm.source"
              type="text"
              placeholder="Journal, publisher, or site name"
              class="min-w-0 flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
            />
            <input
              v-model="sourceForm.url"
              type="text"
              placeholder="URL or DOI link (optional)"
              class="min-w-0 flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-primary-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
            />
          </div>
          <div class="flex gap-2">
            <button
              :disabled="!sourceForm.authors.trim() && !sourceForm.title.trim()"
              class="rounded bg-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-300 disabled:opacity-50 dark:bg-slate-600 dark:text-slate-200 dark:hover:bg-slate-500"
              @click="addOrUpdateSource"
            >
              {{ editingSourceId ? "Update" : "Add" }}
            </button>
            <button
              v-if="editingSourceId"
              class="rounded px-3 py-1.5 text-sm text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              @click="resetSourceForm"
            >
              Cancel
            </button>
          </div>
        </div>
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
