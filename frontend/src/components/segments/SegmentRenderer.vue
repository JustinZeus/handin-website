<script setup lang="ts">
import type { Segment } from "@/types/segment";
import MarkdownSegment from "@/components/segments/MarkdownSegment.vue";
import PdfSegment from "@/components/segments/PdfSegment.vue";
import VideoSegment from "@/components/segments/VideoSegment.vue";
import AudioSegment from "@/components/segments/AudioSegment.vue";
import IframeSegment from "@/components/segments/IframeSegment.vue";
import GallerySegment from "@/components/segments/GallerySegment.vue";
import SourcesSegment from "@/components/segments/SourcesSegment.vue";

defineProps<{
  segment: Segment;
}>();
</script>

<template>
  <MarkdownSegment v-if="segment.type === 'markdown'" :segment="segment" />
  <PdfSegment v-else-if="segment.type === 'pdf'" :segment="segment" />
  <VideoSegment v-else-if="segment.type === 'video'" :segment="segment" />
  <AudioSegment v-else-if="segment.type === 'audio'" :segment="segment" />
  <IframeSegment v-else-if="segment.type === 'iframe'" :segment="segment" />
  <GallerySegment v-else-if="segment.type === 'gallery'" :segment="segment" />
  <SourcesSegment v-else-if="segment.type === 'sources'" :segment="segment" />
</template>
