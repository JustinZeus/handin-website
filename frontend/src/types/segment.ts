export type SegmentType = "markdown" | "pdf" | "video" | "audio" | "iframe" | "gallery" | "team" | "sources";

export interface Source {
  id: string;
  authors: string;
  year: string;
  title: string;
  source: string;
  url: string;
}

export interface Segment {
  id: string;
  type: SegmentType;
  sort_order: number;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
  page_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SiteInfo {
  title: string;
}

export interface Page {
  id: string;
  name: string;
  slug: string;
  sort_order: number;
  is_system: boolean;
  is_hidden: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  name: string;
  student_number: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}
