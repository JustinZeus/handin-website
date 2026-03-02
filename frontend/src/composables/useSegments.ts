import { ref, onMounted } from "vue";
import type { Segment, SiteInfo } from "@/types/segment";

export function useSegments() {
  const segments = ref<Segment[]>([]);
  const siteTitle = ref("Handin");
  const loading = ref(true);
  const error = ref<string | null>(null);

  async function refresh(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const [siteRes, segmentsRes] = await Promise.all([
        fetch("/api/site/"),
        fetch("/api/segments/"),
      ]);
      if (!siteRes.ok) throw new Error(`Site fetch failed: ${siteRes.status}`);
      if (!segmentsRes.ok) throw new Error(`Segments fetch failed: ${segmentsRes.status}`);

      const siteData = (await siteRes.json()) as SiteInfo;
      const segmentsData = (await segmentsRes.json()) as Segment[];

      siteTitle.value = siteData.title;
      segments.value = segmentsData.sort((a, b) => a.sort_order - b.sort_order);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  onMounted(() => {
    void refresh();
  });

  return { segments, siteTitle, loading, error, refresh };
}
