<script setup lang="ts">
import { ref, watch } from "vue";
import type { Segment } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";
import SegmentRenderer from "@/components/segments/SegmentRenderer.vue";
import SegmentEditor from "@/components/admin/SegmentEditor.vue";
import draggable from "vuedraggable";

const props = defineProps<{
  segments: Segment[];
}>();

const emit = defineEmits<{
  save: [id: string, updates: { title?: string; content?: string; metadata?: Record<string, unknown> }];
  delete: [id: string];
  reorder: [ids: string[]];
}>();

const { isAdmin } = useAdmin();
const editingId = ref<string | null>(null);

const localSegments = ref<Segment[]>([...props.segments]);

watch(
  () => props.segments,
  (val) => { localSegments.value = [...val]; },
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
  emit("reorder", localSegments.value.map((s) => s.id));
}
</script>

<template>
  <!-- Admin: draggable flowing sections -->
  <draggable
    v-if="isAdmin"
    v-model="localSegments"
    item-key="id"
    handle=".drag-handle"
    :animation="150"
    :force-fallback="false"
    ghost-class="drag-ghost"
    chosen-class="drag-chosen"
    class="segment-list"
    @end="onDragEnd"
  >
    <template #item="{ element: segment }: { element: Segment }">
      <section :id="segment.id" class="py-8 first:pt-0">
        <div class="flex items-start gap-3">
          <!-- Drag handle -->
          <button
            class="drag-handle mt-1 shrink-0 cursor-grab text-gray-300 transition-colors hover:text-primary-300 active:cursor-grabbing dark:text-gray-700 dark:hover:text-primary-400"
            title="Drag to reorder"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="9" cy="6" r="1.5" /><circle cx="15" cy="6" r="1.5" />
              <circle cx="9" cy="12" r="1.5" /><circle cx="15" cy="12" r="1.5" />
              <circle cx="9" cy="18" r="1.5" /><circle cx="15" cy="18" r="1.5" />
            </svg>
          </button>

          <div class="min-w-0 flex-1">
            <div class="mb-3 flex items-center justify-between gap-2">
              <h2 v-if="segment.title" class="text-xl font-semibold text-gray-900 dark:text-gray-100">{{ segment.title }}</h2>
              <span v-else class="flex-1" />
              <button
                class="shrink-0 rounded p-1.5 text-gray-300 transition-colors hover:bg-gray-100 hover:text-primary-400 dark:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-primary-400"
                :title="editingId === segment.id ? 'Close editor' : 'Edit section'"
                @click="toggleEdit(segment.id)"
              >
                <svg v-if="editingId !== segment.id" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Inline editor replaces content -->
            <SegmentEditor
              v-if="editingId === segment.id"
              :segment="segment"
              @save="(updates) => handleSave(segment.id, updates)"
              @cancel="editingId = null"
              @delete="handleDelete(segment.id)"
            />
            <SegmentRenderer v-else :segment="segment" />
          </div>
        </div>
      </section>
    </template>
  </draggable>

  <!-- Read-only: flowing sections -->
  <div v-else class="segment-list">
    <section
      v-for="segment in segments"
      :key="segment.id"
      :id="segment.id"
      class="py-8 first:pt-0"
    >
      <h2 v-if="segment.title" class="mb-3 text-xl font-semibold text-gray-900 dark:text-gray-100">{{ segment.title }}</h2>
      <SegmentRenderer :segment="segment" />
    </section>
  </div>
</template>

<style scoped>
.segment-list > * + * {
  border-top: 2px solid transparent;
  border-image: linear-gradient(to right, transparent, #d1d5db 20%, #d1d5db 80%, transparent) 1;
}

:global(.dark) .segment-list > * + * {
  border-image: linear-gradient(to right, transparent, #374151 20%, #374151 80%, transparent) 1;
}

.drag-ghost {
  opacity: 0.4;
}
.drag-chosen {
  box-shadow: 0 4px 16px rgb(0 0 0 / 0.1);
}
</style>
