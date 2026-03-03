import { ref } from "vue";
import type { TeamMember } from "@/types/segment";
import { useAdmin } from "@/composables/useAdmin";

export function useTeamMembers() {
  const { authHeaders } = useAdmin();
  const members = ref<TeamMember[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchMembers(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch("/api/team/");
      if (!res.ok) throw new Error(`Failed to fetch team: ${res.status}`);
      members.value = (await res.json()) as TeamMember[];
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  async function addMember(name: string, student_number: string): Promise<TeamMember | null> {
    try {
      const res = await fetch("/api/team/", {
        method: "POST",
        headers: { ...authHeaders.value, "Content-Type": "application/json" },
        body: JSON.stringify({ name, student_number }),
      });
      if (!res.ok) throw new Error(`Add failed: ${res.status}`);
      const member = (await res.json()) as TeamMember;
      await fetchMembers();
      return member;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Unknown error";
      return null;
    }
  }

  async function deleteMember(id: string): Promise<boolean> {
    try {
      const res = await fetch(`/api/team/${id}`, {
        method: "DELETE",
        headers: authHeaders.value,
      });
      if (!res.ok) return false;
      await fetchMembers();
      return true;
    } catch {
      return false;
    }
  }

  return { members, loading, error, fetchMembers, addMember, deleteMember };
}
