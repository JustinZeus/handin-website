<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useRoute } from "vue-router";
import { usePages } from "@/composables/usePages";
import { useAdmin } from "@/composables/useAdmin";
import type { Page, Segment, SegmentType } from "@/types/segment";
import SegmentList from "@/components/segments/SegmentList.vue";
import AddSegmentModal from "@/components/admin/AddSegmentModal.vue";
import TeamPage from "@/views/TeamPage.vue";

const route = useRoute();
const { pages } = usePages();
const { authHeaders, isAdmin } = useAdmin();

const currentPage = ref<Page | null>(null);
const segments = ref<Segment[]>([]);
const loading = ref(false);
const segmentError = ref<string | null>(null);
const showAddModal = ref(false);
const pageNotFound = ref(false);

async function fetchSegments(pageId: string) {
  loading.value = true;
  segmentError.value = null;
  try {
    const res = await fetch(`/api/segments/?page_id=${encodeURIComponent(pageId)}`);
    if (!res.ok) throw new Error(`Failed to load: ${res.status}`);
    const data = (await res.json()) as Segment[];
    segments.value = data.sort((a, b) => a.sort_order - b.sort_order);
  } catch (e) {
    segmentError.value = e instanceof Error ? e.message : "Unknown error";
  } finally {
    loading.value = false;
  }
}

function resolvePage(slug: string) {
  if (!pages.value.length) return;
  pageNotFound.value = false;
  const found = pages.value.find((p) => p.slug === slug);
  if (found) {
    currentPage.value = found;
    void fetchSegments(found.id);
  } else {
    currentPage.value = null;
    pageNotFound.value = true;
  }
}

watch(() => route.params.slug as string, (slug) => { resolvePage(slug); }, { immediate: true });
watch(pages, () => { resolvePage(route.params.slug as string); });

async function handleCreateSegment(data: {
  type: SegmentType;
  title: string;
  content: string;
  metadata?: Record<string, unknown>;
}) {
  if (!currentPage.value) return;
  const res = await fetch("/api/segments/", {
    method: "POST",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, page_id: currentPage.value.id }),
  });
  if (res.ok) {
    showAddModal.value = false;
    await fetchSegments(currentPage.value.id);
  }
}

async function handleSaveSegment(
  id: string,
  updates: { title?: string; content?: string; metadata?: Record<string, unknown> }
) {
  if (!currentPage.value || Object.keys(updates).length === 0) return;
  const res = await fetch(`/api/segments/${id}`, {
    method: "PATCH",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (res.ok) await fetchSegments(currentPage.value.id);
}

async function handleDeleteSegment(id: string) {
  if (!currentPage.value) return;
  const res = await fetch(`/api/segments/${id}`, {
    method: "DELETE",
    headers: authHeaders.value,
  });
  if (res.ok) await fetchSegments(currentPage.value.id);
}

async function handleReorder(ids: string[]) {
  if (!currentPage.value) return;
  const res = await fetch("/api/segments/reorder", {
    method: "PUT",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify({ segment_ids: ids }),
  });
  if (res.ok) await fetchSegments(currentPage.value.id);
}
</script>

<template>
  <!-- Not found -->
  <div v-if="pageNotFound" class="flex flex-col items-center justify-center py-32 text-gray-400">
    <p class="text-lg">Page not found.</p>
  </div>

  <!-- Waiting for pages to load -->
  <div v-else-if="!currentPage && !pageNotFound" class="flex items-center justify-center py-32">
    <svg class="h-8 w-8 animate-spin text-primary-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  </div>

  <!-- Page content -->
  <template v-else-if="currentPage">
    <!-- Team system page -->
    <TeamPage v-if="currentPage.slug === 'team'" />

    <!-- Regular page -->
    <template v-else>
      <!-- Loading segments -->
      <div v-if="loading" class="flex items-center justify-center py-32">
        <svg class="h-8 w-8 animate-spin text-primary-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Error -->
      <div v-else-if="segmentError" class="flex items-center justify-center py-32">
        <p class="text-lg text-red-500">{{ segmentError }}</p>
      </div>

      <!-- Empty page -->
      <div
        v-else-if="!segments.length"
        class="flex flex-col items-center justify-center py-32 text-gray-400 dark:text-gray-600"
      >
        <svg class="mb-4 h-14 w-14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="mb-1 text-base font-medium">This page is empty</p>
        <p v-if="isAdmin" class="text-sm">Use the <strong>+ Add section</strong> button to add your first section.</p>
      </div>

      <!-- Segment list -->
      <SegmentList
        v-else
        :segments="segments"
        @save="handleSaveSegment"
        @delete="handleDeleteSegment"
        @reorder="handleReorder"
      />
    </template>
  </template>

  <!-- Floating "Add section" FAB (admin only) -->
  <Teleport to="body">
    <button
      v-if="isAdmin && currentPage && currentPage.slug !== 'team'"
      class="fixed right-6 bottom-6 z-30 flex items-center gap-2 rounded-full bg-primary-300 px-5 py-3 font-medium text-gray-900 shadow-lg transition-all hover:bg-primary-400 hover:shadow-xl active:scale-95"
      title="Add a new section to this page"
      @click="showAddModal = true"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Add section
    </button>
  </Teleport>

  <!-- Add segment modal -->
  <AddSegmentModal
    v-if="showAddModal"
    @create="handleCreateSegment"
    @cancel="showAddModal = false"
  />
</template>
