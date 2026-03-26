import type { Source } from "@/types/segment";

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatUrl(url: string): string {
  const escaped = escapeHtml(url);
  return `<a href="${escaped}" target="_blank" rel="noopener noreferrer" class="text-primary-600 underline break-all dark:text-primary-400">${escaped}</a>`;
}

export function formatApaCitation(source: Source): string {
  const parts: string[] = [];

  if (source.authors) {
    const authors = escapeHtml(source.authors);
    parts.push(authors.endsWith(".") ? authors : `${authors}.`);
  }

  parts.push(`(${escapeHtml(source.year || "n.d.")}).`);

  if (source.title) {
    const title = escapeHtml(source.title);
    parts.push(title.endsWith(".") ? `<em>${title}</em>` : `<em>${title}</em>.`);
  }

  if (source.source) {
    const src = escapeHtml(source.source);
    parts.push(src.endsWith(".") ? `<em>${src}</em>` : `<em>${src}</em>.`);
  }

  if (source.url) {
    parts.push(formatUrl(source.url));
  }

  return parts.join(" ").replace(/\.\./g, ".");
}
