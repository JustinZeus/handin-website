export type SegmentType = "markdown" | "pdf" | "video" | "audio" | "iframe" | "gallery" | "link";

export interface Segment {
  id: string;
  type: SegmentType;
  sort_order: number;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SiteInfo {
  title: string;
}
