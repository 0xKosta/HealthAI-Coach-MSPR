<template>
  <div class="max-w-lg mx-auto space-y-6 animate-fade-in pb-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-brand-primary">Communauté</h1>
        <p class="text-slate-600 text-sm mt-1">Partagez vos succès et encouragez les autres</p>
      </div>
      <RouterLink
        v-if="profileLink"
        :to="profileLink"
        class="btn-secondary text-sm shrink-0"
        aria-label="Paramètres du profil"
      >
        Profil
      </RouterLink>
    </div>

    <PwaInstallBanner />

    <section class="card space-y-4" aria-label="Nouvelle publication">
      <h2 class="text-lg font-bold text-brand-primary">Publier</h2>
      <form class="space-y-3" @submit.prevent="submitPost">
        <div>
          <label class="label" for="post-content">Message</label>
          <textarea
            id="post-content"
            v-model.trim="newPost.content"
            rows="3"
            class="input resize-y min-h-[88px]"
            placeholder="Partagez une victoire ou une difficulté…"
            maxlength="2000"
          />
        </div>
        <div>
          <label class="label" for="post-media">Photo ou vidéo (optionnel)</label>
          <input
            id="post-media"
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4"
            class="input text-sm"
            @change="onFileChange"
          />
        </div>
        <ErrorAlert v-if="postError" :message="postError" />
        <button type="submit" class="btn-primary w-full justify-center" :disabled="posting">
          {{ posting ? 'Publication…' : 'Publier' }}
        </button>
      </form>
    </section>

    <LoadingSpinner v-if="loading" message="Chargement du fil…" />
    <ErrorAlert v-else-if="loadError" :message="loadError" />

    <p v-else-if="posts.length === 0" class="text-center text-slate-500 text-sm py-8">
      Aucune publication pour le moment. Soyez le premier !
    </p>

    <article
      v-for="post in posts"
      :key="post.id"
      class="card space-y-3"
      :aria-label="`Publication de ${post.first_name} ${post.last_name}`"
    >
      <header class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary font-semibold text-sm shrink-0"
          aria-hidden="true"
        >
          {{ initials(post) }}
        </div>
        <div class="min-w-0 flex-1">
          <p class="font-semibold text-brand-primary truncate">
            {{ post.first_name }} {{ post.last_name }}
          </p>
          <time class="text-xs text-slate-500" :datetime="post.created_at">
            {{ formatDate(post.created_at) }}
          </time>
        </div>
        <button
          v-if="post.author_id === auth.currentUser?.id"
          type="button"
          class="text-xs text-red-600 hover:underline"
          @click="removePost(post.id)"
        >
          Supprimer
        </button>
      </header>

      <p v-if="post.content" class="text-slate-700 whitespace-pre-wrap break-words">
        {{ post.content }}
      </p>

      <img
        v-if="post.media_url && post.media_type === 'image'"
        :src="mediaUrl(post.media_url)"
        alt="Média de la publication"
        class="w-full rounded-lg max-h-80 object-cover"
        loading="lazy"
      />
      <video
        v-else-if="post.media_url && post.media_type === 'video'"
        :src="mediaUrl(post.media_url)"
        controls
        class="w-full rounded-lg max-h-80"
      />

      <div class="flex items-center gap-4 pt-1 border-t border-slate-100">
        <button
          type="button"
          class="flex items-center gap-1.5 text-sm font-medium transition-colors min-h-[44px] px-2"
          :class="post.liked_by_me ? 'text-brand-accent' : 'text-slate-600 hover:text-brand-accent'"
          :aria-pressed="post.liked_by_me"
          :aria-label="`${post.like_count} likes`"
          @click="toggleLike(post)"
        >
          <span class="material-symbols-outlined text-[22px]" aria-hidden="true">
            {{ post.liked_by_me ? 'favorite' : 'favorite_border' }}
          </span>
          {{ post.like_count }}
        </button>
        <button
          type="button"
          class="flex items-center gap-1.5 text-sm text-slate-600 hover:text-brand-primary min-h-[44px] px-2"
          :aria-expanded="expandedPostId === post.id"
          @click="toggleComments(post.id)"
        >
          <span class="material-symbols-outlined text-[22px]" aria-hidden="true">chat_bubble_outline</span>
          {{ post.comment_count }}
        </button>
      </div>

      <div v-if="expandedPostId === post.id" class="space-y-3 pt-2">
        <ul v-if="commentsByPost[post.id]?.length" class="space-y-2">
          <li
            v-for="c in commentsByPost[post.id]"
            :key="c.id"
            class="bg-slate-50 rounded-lg px-3 py-2 text-sm"
          >
            <span class="font-medium text-brand-primary">{{ c.first_name }} {{ c.last_name }}</span>
            <span class="text-slate-500 text-xs ml-2">{{ formatDate(c.created_at) }}</span>
            <p class="text-slate-700 mt-1 break-words">{{ c.content }}</p>
          </li>
        </ul>
        <form class="flex gap-2" @submit.prevent="submitComment(post.id)">
          <label class="sr-only" :for="`comment-${post.id}`">Commentaire</label>
          <input
            :id="`comment-${post.id}`"
            v-model="commentDrafts[post.id]"
            type="text"
            class="input flex-1 text-sm"
            placeholder="Écrire un commentaire…"
            maxlength="2000"
            required
          />
          <button type="submit" class="btn-primary text-sm shrink-0" :disabled="commentingId === post.id">
            Envoyer
          </button>
        </form>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { API_BASE_URL, postsAPI } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { useDashboardScope } from '@/composables/useDashboardScope'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import PwaInstallBanner from '@/components/ui/PwaInstallBanner.vue'

const route = useRoute()
const auth = useAuthStore()
const { basePath } = useDashboardScope()

const loading = ref(true)
const loadError = ref('')
const posts = ref([])
const posting = ref(false)
const postError = ref('')
const expandedPostId = ref(null)
const commentsByPost = reactive({})
const commentDrafts = reactive({})
const commentingId = ref(null)

const newPost = ref({ content: '', file: null })

const profileLink = computed(() => {
  const uid = route.params.userId
  if (!uid) return null
  return `${basePath(uid)}/profile`
})

function mediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const base = API_BASE_URL.replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

function initials(post) {
  const a = post.first_name?.[0] || ''
  const b = post.last_name?.[0] || ''
  return (a + b).toUpperCase() || '?'
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

async function loadFeed() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await postsAPI.getFeed({ limit: 50 })
    posts.value = data
  } catch (e) {
    loadError.value = e.response?.data?.detail || 'Impossible de charger le fil.'
  } finally {
    loading.value = false
  }
}

function onFileChange(event) {
  const file = event.target.files?.[0]
  newPost.value.file = file || null
}

async function submitPost() {
  if (!newPost.value.content && !newPost.value.file) {
    postError.value = 'Ajoutez un texte ou une image.'
    return
  }
  posting.value = true
  postError.value = ''
  try {
    const form = new FormData()
    if (newPost.value.content) form.append('content', newPost.value.content)
    if (newPost.value.file) form.append('media', newPost.value.file)
    await postsAPI.create(form)
    newPost.value = { content: '', file: null }
    await loadFeed()
  } catch (e) {
    postError.value = e.response?.data?.detail || 'Échec de la publication.'
  } finally {
    posting.value = false
  }
}

async function toggleLike(post) {
  try {
    const { data } = await postsAPI.toggleLike(post.id)
    post.liked_by_me = data.liked
    post.like_count = data.like_count
  } catch {
    /* ignore */
  }
}

async function toggleComments(postId) {
  if (expandedPostId.value === postId) {
    expandedPostId.value = null
    return
  }
  expandedPostId.value = postId
  if (!commentsByPost[postId]) {
    try {
      const { data } = await postsAPI.getComments(postId)
      commentsByPost[postId] = data
    } catch {
      commentsByPost[postId] = []
    }
  }
}

async function submitComment(postId) {
  const text = (commentDrafts[postId] || '').trim()
  if (!text) return
  commentingId.value = postId
  try {
    const { data } = await postsAPI.addComment(postId, text)
    if (!commentsByPost[postId]) commentsByPost[postId] = []
    commentsByPost[postId].push(data)
    commentDrafts[postId] = ''
    const row = posts.value.find((p) => p.id === postId)
    if (row) row.comment_count += 1
  } catch {
    /* ignore */
  } finally {
    commentingId.value = null
  }
}

async function removePost(postId) {
  if (!confirm('Supprimer cette publication ?')) return
  try {
    await postsAPI.deletePost(postId)
    posts.value = posts.value.filter((p) => p.id !== postId)
  } catch {
    /* ignore */
  }
}

onMounted(loadFeed)
</script>
