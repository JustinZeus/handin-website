<script setup lang="ts">
import { ref, watch, computed } from "vue";
import type { Segment } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";
import SegmentRenderer from "@/components/segments/SegmentRenderer.vue";
import SegmentEditor from "@/components/admin/SegmentEditor.vue";
import draggable from "vuedraggable";

const props = defineProps<{
  segments: Segment[];
}>();

// Filter out link segments from content rendering (they only appear in nav)
const contentSegments = computed(() => props.segments.filter((s) => s.type !== "link"));

const emit = defineEmits<{
  save: [id: string, updates: { title?: string; content?: string; metadata?: Record<string, unknown> }];
  delete: [id: string];
  reorder: [ids: string[]];
}>();

const { isAdmin } = useAdmin();
const editingId = ref<string | null>(null);

// Local copy for draggable
const localSegments = ref<Segment[]>([...props.segments]);

watch(
  () => props.segments,
  (val) => {
    localSegments.value = [...val];
  },
  { deep: true }
);

function toggleEdit(id: string) {
  editingId.value = editingId.value === id ? null : id;
}

function handleSave(
  id: string,
  updates: { title?: string; content?: string; metadata?: Record<string, unknown> }
) {
  editingId.value = null;
  emit("save", id, updates);
}

function handleDelete(id: string) {
  editingId.value = null;
  emit("delete", id);
}

function onDragEnd() {
  const ids = localSegments.value.map((s) => s.id);
  emit("reorder", ids);
}
</script>

<template>
  <div class="space-y-6 p-6">
    <!-- Admin mode: draggable with edit controls -->
    <draggable
      v-if="isAdmin"
      v-model="localSegments"
      item-key="id"
      handle=".drag-handle"
      class="space-y-6"
      @end="onDragEnd"
    >
      <template #item="{ element: segment }: { element: Segment }">
        <section
          :id="segment.id"
          class="rounded-lg bg-white p-6 shadow-md dark:bg-slate-800 dark:shadow-slate-950/30"
        >
          <div class="flex items-start gap-3">
            <!-- Drag handle: grip dots -->
            <button
              class="drag-handle mt-1 cursor-grab text-slate-300 transition-colors hover:text-primary-300 active:cursor-grabbing dark:text-slate-600 dark:hover:text-primary-400"
              title="Drag to reorder"
            >
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="9" cy="6" r="1.5" />
                <circle cx="15" cy="6" r="1.5" />
                <circle cx="9" cy="12" r="1.5" />
                <circle cx="15" cy="12" r="1.5" />
                <circle cx="9" cy="18" r="1.5" />
                <circle cx="15" cy="18" r="1.5" />
              </svg>
            </button>

            <div class="min-w-0 flex-1">
              <div class="mb-4 flex items-center justify-between">
                <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">{{ segment.title }}</h2>
                <!-- Edit pencil icon -->
                <button
                  class="rounded p-1 text-slate-300 transition-colors hover:text-primary-300 dark:text-slate-600 dark:hover:text-primary-400"
                  title="Edit segment"
                  @click="toggleEdit(segment.id)"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              </div>

              <!-- Link segments show URL instead of content -->
              <p v-if="segment.type === 'link'" class="text-sm text-slate-400">
                External link: <a :href="segment.content" target="_blank" rel="noopener noreferrer" class="text-primary-500 underline">{{ segment.content }}</a>
              </p>
              <SegmentRenderer v-else :segment="segment" />

              <!-- Inline editor -->
              <SegmentEditor
                v-if="editingId === segment.id"
                :segment="segment"
                @save="(updates) => handleSave(segment.id, updates)"
                @cancel="editingId = null"
                @delete="handleDelete(segment.id)"
              />
            </div>
          </div>
        </section>
      </template>
    </draggable>

    <!-- Read-only mode: plain rendering (link segments excluded) -->
    <template v-else>
      <section
        v-for="segment in contentSegments"
        :key="segment.id"
        :id="segment.id"
        class="rounded-lg bg-white p-6 shadow-md dark:bg-slate-800 dark:shadow-slate-950/30"
      >
        <h2 class="mb-4 text-xl font-semibold text-slate-900 dark:text-slate-100">{{ segment.title }}</h2>
        <SegmentRenderer :segment="segment" />
      </section>
    </template>
  </div>
</template>
