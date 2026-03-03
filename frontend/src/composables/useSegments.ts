import { ref } from "vue";
import type { Segment } from "@/types/segment";

export function useSegments(pageId: string) {
  const segments = ref<Segment[]>([]);
  const loading = ref(true);
  const error = ref<string | null>(null);

  async function refresh(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`/api/segments/?page_id=${encodeURIComponent(pageId)}`);
      if (!res.ok) throw new Error(`Segments fetch failed: ${res.status}`);
      const data = (await res.json()) as Segment[];
      segments.value = data.sort((a, b) => a.sort_order - b.sort_order);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  return { segments, loading, error, refresh };
}
