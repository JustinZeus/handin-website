import { ref } from "vue";
import type { Page } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";

const pages = ref<Page[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

export function usePages() {
  const { authHeaders } = useAdmin();

  async function fetchPages(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch("/api/pages/");
      if (!res.ok) throw new Error(`Failed to fetch pages: ${res.status}`);
      pages.value = (await res.json()) as Page[];
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  async function createPage(name: string, slug: string): Promise<Page | null> {
    try {
      const res = await fetch("/api/pages/", {
        method: "POST",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify({ name, slug }),
      });
      if (!res.ok) {
        const data = (await res.json()) as { detail?: string };
        throw new Error(data.detail ?? `Create failed: ${res.status}`);
      }
      const page = (await res.json()) as Page;
      await fetchPages();
      return page;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
      return null;
    }
  }

  async function updatePage(id: string, data: { name?: string; slug?: string }): Promise<Page | null> {
    try {
      const res = await fetch(`/api/pages/${id}`, {
        method: "PATCH",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const body = (await res.json()) as { detail?: string };
        throw new Error(body.detail ?? `Update failed: ${res.status}`);
      }
      const page = (await res.json()) as Page;
      await fetchPages();
      return page;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
      return null;
    }
  }

  async function deletePage(id: string): Promise<{ ok: boolean; error?: string }> {
    try {
      const res = await fetch(`/api/pages/${id}`, {
        method: "DELETE",
        headers: authHeaders.value,
      });
      if (!res.ok) {
        const body = (await res.json()) as { detail?: string };
        return { ok: false, error: body.detail ?? `Delete failed: ${res.status}` };
      }
      await fetchPages();
      return { ok: true };
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      return { ok: false, error: msg };
    }
  }

  async function toggleHidden(id: string, hidden: boolean): Promise<void> {
    try {
      await fetch(`/api/pages/${id}`, {
        method: "PATCH",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify({ is_hidden: hidden }),
      });
      await fetchPages();
    } catch { /* Silently fail */ }
  }

  async function reorderPages(ids: string[]): Promise<void> {
    try {
      const res = await fetch("/api/pages/reorder", {
        method: "PUT",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify({ page_ids: ids }),
      });
      if (!res.ok) throw new Error(`Reorder failed: ${res.status}`);
      pages.value = (await res.json()) as Page[];
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    }
  }

  return { pages, loading, error, fetchPages, createPage, updatePage, deletePage, reorderPages, toggleHidden };
}
