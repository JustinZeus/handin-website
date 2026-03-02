import { ref } from "vue";

export function useAssetUpload() {
  const uploading = ref(false);
  const error = ref<string | null>(null);

  async function upload(
    file: File,
    authHeaders: Record<string, string>
  ): Promise<string | null> {
    uploading.value = true;
    error.value = null;

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/assets/", {
        method: "POST",
        headers: authHeaders,
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Upload failed" }));
        const detail = (body as { detail?: string }).detail ?? "Upload failed";
        error.value = detail;
        return null;
      }

      const data = (await res.json()) as { filename: string };
      return data.filename;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Upload failed";
      return null;
    } finally {
      uploading.value = false;
    }
  }

  return { uploading, error, upload };
}
