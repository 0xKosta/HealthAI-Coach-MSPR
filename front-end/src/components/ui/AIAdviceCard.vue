<template>
  <div class="ai-card animate-slide-up">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 rounded-xl bg-brand-accent/20 border border-brand-accent/40 flex items-center justify-center">
        <svg class="w-5 h-5 text-brand-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/><circle cx="18" cy="6" r="3" fill="currentColor"/>
        </svg>
      </div>
      <div>
        <p class="text-xs font-semibold text-brand-accent uppercase tracking-wider">Coach IA</p>
        <p class="text-sm font-semibold text-slate-200">{{ title }}</p>
      </div>
      <span class="ml-auto badge-accent">GPT-4o</span>
    </div>

    <!-- Content -->
    <div class="ai-prose" v-html="formattedContent"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Analyse personnalisée' },
  content: { type: String, required: true }
})

const formattedContent = computed(() => {
  if (!props.content) return ''
  return props.content
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^#####\s+(.+)$/gm, '<h5 class="ai-heading">$1</h5>')
    .replace(/^####\s+(.+)$/gm, '<h4 class="ai-heading">$1</h4>')
    .replace(/^###\s+(.+)$/gm, '<h3 class="ai-heading">$1</h3>')
    .replace(/^##\s+(.+)$/gm, '<h2 class="ai-heading">$1</h2>')
    .replace(/^#\s+(.+)$/gm, '<h1 class="ai-heading">$1</h1>')
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]+?<\/li>)/g, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
})
</script>
