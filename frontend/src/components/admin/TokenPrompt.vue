<script setup lang="ts">
import { ref } from "vue";
import { useAdmin } from "@/composables/useAdmin";

const { isAdmin, verifying, login } = useAdmin();

const emit = defineEmits<{
  authenticated: [];
}>();

const showInput = ref(false);
const tokenInput = ref("");
const loginError = ref(false);

async function handleSubmit() {
  loginError.value = false;
  const success = await login(tokenInput.value);
  if (success) {
    showInput.value = false;
    tokenInput.value = "";
    emit("authenticated");
  } else {
    loginError.value = true;
  }
}

function handleCancel() {
  showInput.value = false;
  tokenInput.value = "";
  loginError.value = false;
}
</script>

<template>
  <div v-if="!isAdmin" class="flex items-center">
    <!-- Lock icon button -->
    <button
      v-if="!showInput"
      class="rounded p-1.5 text-slate-700 transition-colors hover:bg-primary-400/30"
      title="Admin login"
      @click="showInput = true"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    </button>

    <!-- Inline token input -->
    <form v-else class="flex items-center gap-2" @submit.prevent="handleSubmit">
      <input
        v-model="tokenInput"
        type="password"
        placeholder="Admin token"
        class="h-8 w-40 rounded border px-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-400 focus:outline-none dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500"
        :class="loginError ? 'border-red-400' : 'border-slate-300 dark:border-slate-600'"
        autofocus
      />
      <button
        type="submit"
        :disabled="verifying || !tokenInput"
        class="h-8 rounded bg-slate-800 px-3 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-600 dark:hover:bg-slate-500"
      >
        {{ verifying ? "..." : "Go" }}
      </button>
      <button
        type="button"
        class="h-8 rounded px-2 text-sm text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        @click="handleCancel"
      >
        &times;
      </button>
    </form>
  </div>
</template>
