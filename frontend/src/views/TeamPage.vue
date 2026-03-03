<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useTeamMembers } from "@/composables/useTeamMembers";
import { useAdmin } from "@/composables/useAdmin";

const { members, loading, fetchMembers, addMember, deleteMember } = useTeamMembers();
const { isAdmin } = useAdmin();

const newName = ref("");
const newNumber = ref("");
const adding = ref(false);
const addError = ref<string | null>(null);

onMounted(() => { void fetchMembers(); });

async function handleAdd() {
  const name = newName.value.trim();
  const number = newNumber.value.trim();
  if (!name || !number) return;
  adding.value = true;
  addError.value = null;
  const result = await addMember(name, number);
  adding.value = false;
  if (result) {
    newName.value = "";
    newNumber.value = "";
  } else {
    addError.value = "Could not add member.";
  }
}
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Team Members</h1>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <svg class="h-8 w-8 animate-spin text-primary-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <template v-else>
      <!-- Empty state (non-admin) -->
      <div
        v-if="!members.length && !isAdmin"
        class="flex flex-col items-center justify-center py-24 text-gray-400 dark:text-gray-600"
      >
        <svg class="mb-4 h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="text-base font-medium">No team members yet.</p>
      </div>

      <!-- Member table -->
      <div v-else-if="members.length" class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
              <th class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">Name</th>
              <th class="px-4 py-3 text-left font-mono font-medium text-gray-600 dark:text-gray-300">Student number</th>
              <th v-if="isAdmin" class="w-12 px-4 py-3" />
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr
              v-for="member in members"
              :key="member.id"
              class="bg-white transition-colors hover:bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800/60"
            >
              <td class="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{{ member.name }}</td>
              <td class="px-4 py-3 font-mono text-gray-500 dark:text-gray-400">{{ member.student_number }}</td>
              <td v-if="isAdmin" class="px-4 py-3 text-right">
                <button
                  class="rounded p-1 text-gray-300 transition-colors hover:bg-red-50 hover:text-red-500 dark:text-gray-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                  title="Remove member"
                  @click="deleteMember(member.id)"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add member form (admin) -->
      <form v-if="isAdmin" class="mt-4 flex gap-2" @submit.prevent="handleAdd">
        <input
          v-model="newName"
          type="text"
          placeholder="Full name"
          class="min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
        />
        <input
          v-model="newNumber"
          type="text"
          placeholder="Student number"
          class="w-40 rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-400 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
        />
        <button
          type="submit"
          :disabled="!newName.trim() || !newNumber.trim() || adding"
          class="rounded bg-primary-200 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-primary-300 disabled:opacity-50"
        >
          {{ adding ? "Adding…" : "Add" }}
        </button>
      </form>
      <p v-if="addError" class="mt-1.5 text-xs text-red-600 dark:text-red-400">{{ addError }}</p>
    </template>
  </div>
</template>
