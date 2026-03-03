<script setup lang="ts">
import { ref, nextTick, onMounted, watch, watchEffect } from "vue";
import { useRouter, useRoute } from "vue-router";
import Sidebar from "@/components/layout/Sidebar.vue";
import { usePages } from "@/composables/usePages";
import { useAdmin } from "@/composables/useAdmin";
import type { SiteInfo } from "@/types/segment";
import logoUrl from "@/assets/logo.png";

const router = useRouter();
const route = useRoute();
const { pages, fetchPages } = usePages();
const { isAdmin, authHeaders } = useAdmin();

const mobileNavOpen = ref(false);
const scrolledDown = ref(false);
const mainEl = ref<HTMLElement | null>(null);
const siteTitle = ref("Untitled Site");
const editingSiteTitle = ref(false);
const siteTitleInput = ref("");

async function loadSiteTitle() {
  try {
    const res = await fetch("/api/site/");
    if (res.ok) {
      const data = (await res.json()) as SiteInfo;
      siteTitle.value = data.title;
    }
  } catch { /* Silently fail */ }
}

function startEditTitle() {
  if (!isAdmin.value) return;
  siteTitleInput.value = siteTitle.value;
  editingSiteTitle.value = true;
  nextTick(() => { document.getElementById("header-title-input")?.focus(); });
}

async function saveSiteTitle() {
  const trimmed = siteTitleInput.value.trim();
  if (trimmed && trimmed !== siteTitle.value) {
    try {
      const res = await fetch("/api/site/", {
        method: "PUT",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify({ title: trimmed }),
      });
      if (res.ok) siteTitle.value = trimmed;
    } catch { /* Silently fail */ }
  }
  editingSiteTitle.value = false;
}

// Dynamic browser tab title
watchEffect(() => {
  const slug = route.params.slug as string | undefined;
  const page = slug ? pages.value.find((p) => p.slug === slug) : undefined;
  document.title = page ? `${page.name} | ${siteTitle.value}` : siteTitle.value;
});

// Redirect "/" to first page once pages are loaded
watch(pages, (loaded) => {
  if (loaded.length > 0 && (route.path === "/" || route.path === "")) {
    void router.replace({ name: "page", params: { slug: "home" } });
  }
});

function handleScroll(e: Event) {
  scrolledDown.value = (e.target as HTMLElement).scrollTop > 200;
}

function scrollToTop() {
  mainEl.value?.scrollTo({ top: 0, behavior: "smooth" });
}

onMounted(async () => {
  await Promise.all([loadSiteTitle(), fetchPages()]);
  if (pages.value.length > 0 && (route.path === "/" || route.path === "")) {
    void router.replace({ name: "page", params: { slug: "home" } });
  }
});
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-white dark:bg-gray-900">
    <!-- Full-width yellow header -->
    <header class="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-primary-400 bg-primary-300 px-4">
      <!-- Hamburger (mobile only) -->
      <button
        class="shrink-0 rounded p-1.5 text-gray-700 transition-colors hover:bg-primary-400 md:hidden"
        aria-label="Open navigation"
        @click="mobileNavOpen = true"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Logo -->
      <img :src="logoUrl" alt="Logo" class="h-10 w-auto shrink-0" />

      <!-- Site title -->
      <form v-if="editingSiteTitle" @submit.prevent="saveSiteTitle">
        <input
          id="header-title-input"
          v-model="siteTitleInput"
          type="text"
          class="rounded border border-primary-500 bg-primary-200/60 px-2 py-0.5 text-base font-bold text-gray-900 focus:outline-none"
          @blur="saveSiteTitle"
          @keydown.escape="editingSiteTitle = false"
        />
      </form>
      <div
        v-else
        class="group flex min-w-0 items-center gap-1"
        :class="isAdmin ? 'cursor-pointer' : ''"
        :title="isAdmin ? 'Click to rename' : undefined"
        @click="startEditTitle"
      >
        <span class="truncate text-lg font-bold text-gray-900">{{ siteTitle }}</span>
        <svg
          v-if="isAdmin"
          class="h-3 w-3 shrink-0 text-gray-600 opacity-0 transition-opacity group-hover:opacity-100"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      </div>
    </header>

    <!-- Body: sidebar + scrollable content -->
    <div class="flex min-h-0 flex-1">
      <!-- Mobile sidebar overlay -->
      <Transition name="sidebar-fade">
        <div
          v-if="mobileNavOpen"
          class="fixed inset-0 z-40 bg-black/40 md:hidden"
          @click="mobileNavOpen = false"
        />
      </Transition>

      <!-- Mobile sidebar drawer -->
      <Transition name="sidebar-slide">
        <div
          v-show="mobileNavOpen"
          class="fixed inset-y-0 left-0 z-50 md:hidden"
        >
          <Sidebar @close="mobileNavOpen = false" />
        </div>
      </Transition>

      <!-- Desktop sidebar (always visible) -->
      <div class="hidden md:flex md:shrink-0">
        <Sidebar @close="() => {}" />
      </div>

      <!-- Scrollable content -->
      <main ref="mainEl" class="flex-1 overflow-y-auto" @scroll="handleScroll">
        <div class="mx-auto max-w-5xl px-6 py-10">
          <slot />
        </div>
      </main>
    </div>
  </div>

  <!-- Scroll to top FAB -->
  <Teleport to="body">
    <Transition name="scroll-top-fade">
      <button
        v-if="scrolledDown"
        class="fixed bottom-20 right-6 z-30 flex items-center gap-2 rounded-full bg-primary-300 px-5 py-3 font-medium text-gray-900 shadow-lg transition-all hover:bg-primary-400 hover:shadow-xl active:scale-95"
        aria-label="Scroll to top"
        @click="scrollToTop"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
        Back to top
      </button>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sidebar-fade-enter-active,
.sidebar-fade-leave-active {
  transition: opacity 200ms ease;
}
.sidebar-fade-enter-from,
.sidebar-fade-leave-to {
  opacity: 0;
}

.sidebar-slide-enter-active,
.sidebar-slide-leave-active {
  transition: transform 250ms ease;
}
.sidebar-slide-enter-from,
.sidebar-slide-leave-to {
  transform: translateX(-100%);
}

.scroll-top-fade-enter-active,
.scroll-top-fade-leave-active {
  transition: opacity 200ms ease;
}
.scroll-top-fade-enter-from,
.scroll-top-fade-leave-to {
  opacity: 0;
}
</style>
