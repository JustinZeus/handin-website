<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from "vue";
import { useEditor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "tiptap-markdown";

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const headingDropdownOpen = ref(false);

const headingLevels = [
  { level: 0, label: "Paragraph" },
  { level: 1, label: "Heading 1" },
  { level: 2, label: "Heading 2" },
  { level: 3, label: "Heading 3" },
] as const;

const editor = useEditor({
  extensions: [
    StarterKit,
    Markdown.configure({ html: false, transformPastedText: true }),
  ],
  content: props.modelValue,
  onUpdate() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    emit("update:modelValue", (editor.value?.storage as any).markdown?.getMarkdown() ?? "");
  },
});

function getActiveHeadingLabel() {
  if (!editor.value) return "Paragraph";
  for (const h of headingLevels) {
    if (h.level > 0 && editor.value.isActive("heading", { level: h.level })) return h.label;
  }
  return "Paragraph";
}

function applyHeading(level: 0 | 1 | 2 | 3) {
  headingDropdownOpen.value = false;
  if (!editor.value) return;
  if (level === 0) {
    editor.value.chain().focus().setParagraph().run();
  } else {
    editor.value.chain().focus().toggleHeading({ level }).run();
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (!editor.value) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const current = (editor.value.storage as any).markdown?.getMarkdown() ?? "";
    if (val !== current) {
      editor.value.commands.setContent(val);
    }
  },
);

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<template>
  <div class="rounded border border-gray-300 dark:border-gray-600">
    <!-- Toolbar -->
    <div class="flex flex-wrap items-center gap-0.5 border-b border-gray-300 bg-gray-50 p-1.5 dark:border-gray-600 dark:bg-gray-700/50">
      <!-- Heading dropdown -->
      <div class="relative">
        <button
          type="button"
          class="flex items-center gap-1 rounded px-2 py-1.5 text-xs text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
          :class="editor?.isActive('heading') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
          title="Heading level"
          @click="headingDropdownOpen = !headingDropdownOpen"
        >
          <span class="font-medium">{{ getActiveHeadingLabel() }}</span>
          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div
          v-if="headingDropdownOpen"
          class="absolute left-0 top-full z-10 mt-0.5 min-w-[120px] rounded border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-600 dark:bg-gray-800"
        >
          <button
            v-for="h in headingLevels"
            :key="h.level"
            type="button"
            class="block w-full px-3 py-1.5 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            :class="[
              h.level === 0 ? 'text-gray-700 dark:text-gray-300' : '',
              h.level === 1 ? 'text-base font-bold text-gray-900 dark:text-gray-100' : '',
              h.level === 2 ? 'font-semibold text-gray-900 dark:text-gray-100' : '',
              h.level === 3 ? 'font-medium text-gray-800 dark:text-gray-200' : '',
            ]"
            @click="applyHeading(h.level as 0 | 1 | 2 | 3)"
          >{{ h.label }}</button>
        </div>
      </div>

      <div class="mx-1 h-5 w-px bg-gray-300 dark:bg-gray-600" />

      <!-- Bold -->
      <button
        type="button"
        class="rounded p-1.5 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('bold') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Bold (Ctrl+B)"
        @click="editor?.chain().focus().toggleBold().run()"
      >B</button>
      <!-- Italic -->
      <button
        type="button"
        class="rounded p-1.5 text-sm italic text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('italic') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Italic (Ctrl+I)"
        @click="editor?.chain().focus().toggleItalic().run()"
      >I</button>
      <!-- Strikethrough -->
      <button
        type="button"
        class="rounded p-1.5 text-sm text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('strike') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Strikethrough"
        @click="editor?.chain().focus().toggleStrike().run()"
      ><span class="line-through">S</span></button>
      <!-- Inline code -->
      <button
        type="button"
        class="rounded p-1.5 text-xs font-mono text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('code') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Inline code"
        @click="editor?.chain().focus().toggleCode().run()"
      >&lt;/&gt;</button>

      <div class="mx-1 h-5 w-px bg-gray-300 dark:bg-gray-600" />

      <!-- Bullet list -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('bulletList') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Bullet list"
        @click="editor?.chain().focus().toggleBulletList().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
        </svg>
      </button>
      <!-- Ordered list -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('orderedList') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Ordered list"
        @click="editor?.chain().focus().toggleOrderedList().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 6h13M7 12h13M7 18h13M3 6h.01M3 12h.01M3 18h.01" />
        </svg>
      </button>
      <!-- Blockquote -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('blockquote') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Blockquote"
        @click="editor?.chain().focus().toggleBlockquote().run()"
      >
        <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179z" />
        </svg>
      </button>
      <!-- Code block -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        :class="editor?.isActive('codeBlock') ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300' : ''"
        title="Code block"
        @click="editor?.chain().focus().toggleCodeBlock().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      </button>
      <!-- Horizontal rule -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-600"
        title="Horizontal rule"
        @click="editor?.chain().focus().setHorizontalRule().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14" />
        </svg>
      </button>

      <div class="mx-1 h-5 w-px bg-gray-300 dark:bg-gray-600" />

      <!-- Undo -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 disabled:opacity-30 dark:text-gray-300 dark:hover:bg-gray-600"
        title="Undo (Ctrl+Z)"
        :disabled="!editor?.can().undo()"
        @click="editor?.chain().focus().undo().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6M3 10l6-6" />
        </svg>
      </button>
      <!-- Redo -->
      <button
        type="button"
        class="rounded p-1.5 text-gray-700 transition-colors hover:bg-gray-200 disabled:opacity-30 dark:text-gray-300 dark:hover:bg-gray-600"
        title="Redo (Ctrl+Y)"
        :disabled="!editor?.can().redo()"
        @click="editor?.chain().focus().redo().run()"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6" />
        </svg>
      </button>
    </div>

    <!-- Close heading dropdown on outside click -->
    <div v-if="headingDropdownOpen" class="fixed inset-0 z-0" @click="headingDropdownOpen = false" />

    <!-- Editor content -->
    <EditorContent
      :editor="editor"
      class="min-h-[200px] px-3 py-2 text-sm text-gray-900 dark:text-gray-100 [&_.ProseMirror]:min-h-[180px] [&_.ProseMirror]:outline-none [&_.ProseMirror]:prose [&_.ProseMirror]:dark:prose-invert [&_.ProseMirror]:prose-sm [&_.ProseMirror]:max-w-none"
    />
  </div>
</template>
