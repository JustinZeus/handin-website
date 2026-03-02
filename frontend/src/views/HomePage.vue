<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useSegments } from "@/composables/useSegments";
import { useAdmin } from "@/composables/useAdmin";
import type { SegmentType } from "@/types/segment";
import AppShell from "@/components/layout/AppShell.vue";
import SegmentList from "@/components/segments/SegmentList.vue";
import AddSegmentModal from "@/components/admin/AddSegmentModal.vue";

const { segments, siteTitle, loading, error, refresh } = useSegments();
const { authHeaders, logout } = useAdmin();
const activeId = ref<string | null>(null);
const showAddModal = ref(false);

let observer: IntersectionObserver | null = null;

function handleNavigate(id: string) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth" });
    activeId.value = id;
  }
}

async function handleCreateSegment(data: {
  type: SegmentType;
  title: string;
  content: string;
  metadata?: Record<string, unknown>;
}) {
  const res = await fetch("/api/segments/", {
    method: "POST",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (res.ok) {
    showAddModal.value = false;
    await refresh();
  }
}

async function handleSaveSegment(
  id: string,
  updates: { title?: string; content?: string; metadata?: Record<string, unknown> }
) {
  if (Object.keys(updates).length === 0) return;
  const res = await fetch(`/api/segments/${id}`, {
    method: "PATCH",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (res.ok) {
    await refresh();
  }
}

async function handleDeleteSegment(id: string) {
  const res = await fetch(`/api/segments/${id}`, {
    method: "DELETE",
    headers: authHeaders.value,
  });
  if (res.ok) {
    await refresh();
  }
}

async function handleReorder(ids: string[]) {
  const res = await fetch("/api/segments/reorder", {
    method: "PUT",
    headers: { ...authHeaders.value, "Content-Type": "application/json" },
    body: JSON.stringify({ segment_ids: ids }),
  });
  if (res.ok) {
    await refresh();
  }
}

function handleLogout() {
  logout();
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeId.value = entry.target.id;
        }
      }
    },
    { rootMargin: "-20% 0px -60% 0px" }
  );

  const mutObs = new MutationObserver(() => {
    for (const seg of segments.value) {
      const el = document.getElementById(seg.id);
      if (el) observer?.observe(el);
    }
  });
  mutObs.observe(document.body, { childList: true, subtree: true });

  onUnmounted(() => {
    observer?.disconnect();
    mutObs.disconnect();
  });
});
</script>

<template>
  <AppShell
    :segments="segments"
    :site-title="siteTitle"
    :active-id="activeId"
    @navigate="handleNavigate"
    @add-segment="showAddModal = true"
    @logout="handleLogout"
  >
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-32">
      <svg
        class="h-10 w-10 animate-spin text-primary-300"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex items-center justify-center py-32">
      <p class="text-lg text-red-500">{{ error }}</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="segments.length === 0" class="flex flex-col items-center justify-center py-32 text-slate-400 dark:text-slate-600">
      <svg class="mb-4 h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <p class="text-lg">No content yet</p>
    </div>

    <!-- Segment list -->
    <SegmentList
      v-else
      :segments="segments"
      @save="handleSaveSegment"
      @delete="handleDeleteSegment"
      @reorder="handleReorder"
    />
  </AppShell>

  <!-- Add segment modal -->
  <AddSegmentModal
    v-if="showAddModal"
    @create="handleCreateSegment"
    @cancel="showAddModal = false"
  />
</template>
