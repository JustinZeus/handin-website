<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useRouter, useRoute } from "vue-router";
import draggable from "vuedraggable";
import type { Page } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";
import { usePages } from "@/composables/usePages";
import { useDarkMode } from "@/composables/useDarkMode";

const emit = defineEmits<{
  close: [];
}>();

const router = useRouter();
const route = useRoute();
const { isAdmin, verifying, login, logout } = useAdmin();
const { pages, createPage, updatePage, deletePage, reorderPages, toggleHidden } = usePages();
const { isDark, toggle: toggleDark } = useDarkMode();

// --- Page list drag ---
const localPages = ref<Page[]>(pages.value.filter((p) => !p.is_system));
watch(pages, (val) => { localPages.value = val.filter((p) => !p.is_system); });

function onPageDragEnd() {
  void reorderPages(localPages.value.map((p) => p.id));
}

// --- Page rename ---
const renamingPageId = ref<string | null>(null);
const renameInput = ref("");

function startRename(page: Page) {
  renamingPageId.value = page.id;
  renameInput.value = page.name;
  nextTick(() => { document.getElementById(`rename-input-${page.id}`)?.focus(); });
}

async function saveRename(page: Page) {
  const trimmed = renameInput.value.trim();
  if (trimmed && trimmed !== page.name) {
    const newSlug = trimmed.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    await updatePage(page.id, { name: trimmed, slug: newSlug });
    if (route.params.slug === page.slug) {
      await router.replace({ name: "page", params: { slug: newSlug } });
    }
  }
  renamingPageId.value = null;
}

// --- Delete page ---
async function handleDelete(page: Page) {
  if (!window.confirm(`Pagina "${page.name}" verwijderen?`)) return;
  const result = await deletePage(page.id);
  if (result.ok && route.params.slug === page.slug) {
    const remaining = pages.value.filter((p) => p.id !== page.id);
    if (remaining.length > 0) {
      await router.push({ name: "page", params: { slug: remaining[0].slug } });
    } else {
      await router.push({ name: "page", params: { slug: "home" } });
    }
  }
}

// --- Add page ---
const showAddPage = ref(false);
const newPageName = ref("");
const addPageError = ref<string | null>(null);
const addPageLoading = ref(false);

function openAddPage() {
  showAddPage.value = true;
  newPageName.value = "";
  addPageError.value = null;
  nextTick(() => { document.getElementById("new-page-name")?.focus(); });
}

async function submitAddPage() {
  const name = newPageName.value.trim();
  if (!name) return;
  addPageLoading.value = true;
  addPageError.value = null;
  const slug = name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
  const page = await createPage(name, slug);
  addPageLoading.value = false;
  if (page) {
    showAddPage.value = false;
    await router.push({ name: "page", params: { slug: page.slug } });
  } else {
    addPageError.value = "Could not create page. The name might already be taken.";
  }
}

// --- Admin login (inline) ---
const showLoginInput = ref(false);
const loginTokenInput = ref("");
const loginError = ref(false);

async function handleLogin() {
  loginError.value = false;
  const success = await login(loginTokenInput.value);
  if (success) {
    showLoginInput.value = false;
    loginTokenInput.value = "";
  } else {
    loginError.value = true;
  }
}
</script>

<template>
  <nav class="flex h-full w-52 flex-col border-r border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-700">
    <!-- Pages list (scrollable) -->
    <div class="flex-1 overflow-y-auto py-2">
      <!-- Pinned Home page (always at top, no actions) -->
      <template v-if="pages.find(p => p.slug === 'home')">
        <div class="px-2 py-0.5">
          <router-link
            :to="{ name: 'page', params: { slug: 'home' } }"
            class="flex items-center rounded-md px-2 py-2 text-sm transition-colors"
            :class="
              $route.params.slug === 'home'
                ? 'border-l-2 border-primary-400 bg-primary-50 font-medium text-gray-900 dark:border-primary-400 dark:bg-gray-600 dark:text-white'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:text-white'
            "
            @click="$emit('close')"
          >
            <span v-if="isAdmin" class="w-3.5 shrink-0" />
            <span class="flex-1 truncate">{{ pages.find(p => p.slug === 'home')?.name }}</span>
          </router-link>
        </div>
      </template>

      <!-- Admin draggable user pages (non-system) -->
      <draggable
        v-if="isAdmin"
        v-model="localPages"
        item-key="id"
        handle=".page-drag-handle"
        :animation="150"
        @end="onPageDragEnd"
      >
        <template #item="{ element: page }: { element: Page }">
          <div class="group relative px-2 py-0.5">
            <!-- Rename input -->
            <form v-if="renamingPageId === page.id" @submit.prevent="saveRename(page)">
              <input
                :id="`rename-input-${page.id}`"
                v-model="renameInput"
                type="text"
                class="w-full rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                @blur="saveRename(page)"
                @keydown.escape="renamingPageId = null"
              />
            </form>

            <!-- Normal page row -->
            <router-link
              v-else
              :to="{ name: 'page', params: { slug: page.slug } }"
              class="flex items-center gap-1.5 rounded-md px-2 py-2 text-sm transition-colors"
              :class="[
                $route.params.slug === page.slug
                  ? 'border-l-2 border-primary-400 bg-primary-50 font-medium text-gray-900 dark:border-primary-400 dark:bg-gray-600 dark:text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:text-white',
                page.is_hidden ? 'opacity-50' : '',
              ]"
              @click="$emit('close')"
            >
              <!-- Drag handle -->
              <span class="page-drag-handle shrink-0 cursor-grab text-gray-400 active:cursor-grabbing dark:text-gray-600">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="9" cy="6" r="1.5" /><circle cx="15" cy="6" r="1.5" />
                  <circle cx="9" cy="12" r="1.5" /><circle cx="15" cy="12" r="1.5" />
                  <circle cx="9" cy="18" r="1.5" /><circle cx="15" cy="18" r="1.5" />
                </svg>
              </span>
              <span class="flex-1 truncate">{{ page.name }}</span>
              <span class="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100">
                <!-- Hide/show toggle -->
                <button
                  class="rounded p-0.5 transition-colors"
                  :class="page.is_hidden ? 'text-gray-400 hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-300' : 'text-gray-400 hover:text-gray-700 dark:text-gray-600 dark:hover:text-gray-300'"
                  :title="page.is_hidden ? 'Show page' : 'Hide page'"
                  @click.prevent="toggleHidden(page.id, !page.is_hidden)"
                >
                  <svg v-if="page.is_hidden" class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  <svg v-else class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <!-- Rename -->
                <button
                  class="rounded p-0.5 text-gray-400 hover:text-gray-700 dark:text-gray-600 dark:hover:text-primary-400"
                  title="Rename page"
                  @click.prevent="startRename(page)"
                >
                  <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <!-- Delete -->
                <button
                  class="rounded p-0.5 text-gray-400 hover:text-red-500 dark:text-gray-600 dark:hover:text-red-400"
                  title="Delete page"
                  @click.prevent="handleDelete(page)"
                >
                  <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </span>
            </router-link>
          </div>
        </template>
      </draggable>

      <!-- System pages shown after draggable list (admin), excluding home -->
      <div v-if="isAdmin" v-for="page in pages.filter(p => p.is_system && p.slug !== 'home')" :key="page.id" class="group px-2 py-0.5">
        <router-link
          :to="{ name: 'page', params: { slug: page.slug } }"
          class="flex items-center gap-1.5 rounded-md px-2 py-2 text-sm transition-colors"
          :class="[
            $route.params.slug === page.slug
              ? 'border-l-2 border-primary-400 bg-primary-50 font-medium text-gray-900 dark:border-primary-400 dark:bg-gray-600 dark:text-white'
              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:text-white',
            page.is_hidden ? 'opacity-50' : '',
          ]"
          @click="$emit('close')"
        >
          <span class="w-3.5 shrink-0" />
          <span class="flex-1 truncate">{{ page.name }}</span>
          <span class="flex shrink-0 items-center opacity-0 group-hover:opacity-100">
            <button
              class="rounded p-0.5 transition-colors"
              :class="page.is_hidden ? 'text-gray-400 hover:text-gray-700 dark:text-gray-500 dark:hover:text-gray-300' : 'text-gray-400 hover:text-gray-700 dark:text-gray-600 dark:hover:text-gray-300'"
              :title="page.is_hidden ? 'Show page' : 'Hide page'"
              @click.prevent="toggleHidden(page.id, !page.is_hidden)"
            >
              <svg v-if="page.is_hidden" class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </span>
        </router-link>
      </div>

      <!-- Read-only pages list (non-admin) -->
      <template v-else-if="!isAdmin">
        <!-- Home always shown first -->
        <template v-if="!pages.find(p => p.slug === 'home')">
          <!-- home already rendered above via pinned template -->
        </template>
        <!-- Other non-system, non-hidden pages -->
        <div v-for="page in pages.filter(p => !p.is_hidden && !p.is_system)" :key="page.id" class="px-2 py-0.5">
          <router-link
            :to="{ name: 'page', params: { slug: page.slug } }"
            class="flex items-center rounded-md px-3 py-2 text-sm transition-colors"
            :class="
              $route.params.slug === page.slug
                ? 'border-l-2 border-primary-400 bg-primary-50 font-medium text-gray-900 dark:border-primary-400 dark:bg-gray-600 dark:text-white'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:text-white'
            "
            @click="$emit('close')"
          >
            {{ page.name }}
          </router-link>
        </div>
        <!-- System pages (e.g. team) that are not hidden, excluding home -->
        <div v-for="page in pages.filter(p => !p.is_hidden && p.is_system && p.slug !== 'home')" :key="`sys-${page.id}`" class="px-2 py-0.5">
          <router-link
            :to="{ name: 'page', params: { slug: page.slug } }"
            class="flex items-center rounded-md px-3 py-2 text-sm transition-colors"
            :class="
              $route.params.slug === page.slug
                ? 'border-l-2 border-primary-400 bg-primary-50 font-medium text-gray-900 dark:border-primary-400 dark:bg-gray-600 dark:text-white'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-200 dark:hover:bg-gray-600 dark:hover:text-white'
            "
            @click="$emit('close')"
          >
            {{ page.name }}
          </router-link>
        </div>
      </template>
    </div>

    <!-- Add page (admin only) -->
    <div v-if="isAdmin" class="border-t border-gray-300 p-3 dark:border-gray-600">
      <div v-if="showAddPage">
        <form @submit.prevent="submitAddPage">
          <input
            id="new-page-name"
            v-model="newPageName"
            type="text"
            placeholder="Page name"
            class="mb-1.5 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400"
            @keydown.escape="showAddPage = false"
          />
          <p v-if="addPageError" class="mb-1.5 text-xs text-red-700 dark:text-red-400">{{ addPageError }}</p>
          <div class="flex gap-2">
            <button
              type="submit"
              :disabled="!newPageName.trim() || addPageLoading"
              class="flex-1 rounded bg-primary-200 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-primary-300 disabled:opacity-50"
            >
              {{ addPageLoading ? "Creating..." : "Create page" }}
            </button>
            <button
              type="button"
              class="rounded px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              @click="showAddPage = false"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
      <button
        v-else
        class="flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 transition-colors hover:border-primary-400 hover:bg-primary-50 hover:text-primary-700 dark:border-gray-600 dark:text-gray-400 dark:hover:border-primary-400 dark:hover:text-primary-400"
        @click="openAddPage"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Add new page
      </button>
    </div>

    <!-- Footer: dark mode + auth -->
    <div class="border-t border-gray-300 px-3 py-2 dark:border-gray-600">
      <div class="flex items-center justify-between">
        <!-- Dark mode toggle (icon only) -->
        <button
          class="rounded-md p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-600 dark:hover:text-gray-200"
          :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="toggleDark"
        >
          <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <!-- Logged-in admin: badge + logout -->
        <div v-if="isAdmin" class="flex items-center gap-1.5">
          <span class="rounded bg-gray-900 px-1.5 py-0.5 text-xs font-semibold text-primary-300 dark:bg-primary-400 dark:text-gray-900">Admin</span>
          <button
            class="rounded-md p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-red-500 dark:text-gray-500 dark:hover:bg-gray-600 dark:hover:text-red-400"
            title="Log out"
            @click="logout()"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>

        <!-- Not logged in: lock icon or inline login form -->
        <div v-else>
          <button
            v-if="!showLoginInput"
            class="rounded-md p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-600"
            title="Admin login"
            @click="showLoginInput = true"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Inline login form (expands below the icon row) -->
      <form v-if="!isAdmin && showLoginInput" class="mt-2 space-y-1.5" @submit.prevent="handleLogin">
        <input
          v-model="loginTokenInput"
          type="password"
          placeholder="Admin token"
          autofocus
          class="w-full rounded border px-2 py-1.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400"
          :class="loginError ? 'border-red-400 bg-red-50' : 'border-gray-300 dark:border-gray-600'"
        />
        <p v-if="loginError" class="text-xs text-red-700 dark:text-red-400">Incorrect token.</p>
        <div class="flex gap-2">
          <button
            type="submit"
            :disabled="verifying || !loginTokenInput"
            class="flex-1 rounded bg-primary-200 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-primary-300 disabled:opacity-50 dark:bg-primary-200 dark:text-gray-800 dark:hover:bg-primary-300"
          >
            {{ verifying ? "Checking..." : "Log in" }}
          </button>
          <button
            type="button"
            class="rounded px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            @click="showLoginInput = false; loginTokenInput = ''; loginError = false"
          >
            &times;
          </button>
        </div>
      </form>
    </div>
  </nav>
</template>
