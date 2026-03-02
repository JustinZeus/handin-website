import { ref, computed } from "vue";
import type { Ref, ComputedRef } from "vue";

const token: Ref<string | null> = ref(null);
const isAdmin: Ref<boolean> = ref(false);
const verifying: Ref<boolean> = ref(false);

async function verifyToken(t: string): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/verify", {
      headers: { Authorization: `Bearer ${t}` },
    });
    return res.ok;
  } catch {
    return false;
  }
}

// Check sessionStorage on module load
const stored = sessionStorage.getItem("admin_token");
if (stored) {
  verifying.value = true;
  verifyToken(stored).then((valid) => {
    if (valid) {
      token.value = stored;
      isAdmin.value = true;
    } else {
      sessionStorage.removeItem("admin_token");
    }
    verifying.value = false;
  });
}

export function useAdmin() {
  async function login(t: string): Promise<boolean> {
    verifying.value = true;
    const valid = await verifyToken(t);
    if (valid) {
      token.value = t;
      isAdmin.value = true;
      sessionStorage.setItem("admin_token", t);
    }
    verifying.value = false;
    return valid;
  }

  function logout(): void {
    token.value = null;
    isAdmin.value = false;
    sessionStorage.removeItem("admin_token");
  }

  const authHeaders = computed((): Record<string, string> =>
    token.value ? { Authorization: `Bearer ${token.value}` } : {}
  );

  const authQuery: ComputedRef<string> = computed(() =>
    token.value ? `?token=${encodeURIComponent(token.value)}` : ""
  );

  return { token, isAdmin, verifying, login, logout, authHeaders, authQuery };
}
