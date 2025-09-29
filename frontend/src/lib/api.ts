export type WhoAmI = {
  id: number;
  email: string;
  name?: string;
  avatar_url?: string;
  plan?: "free" | "growth" | "max";
  is_admin?: boolean;
} | null;

const BASE = ""; // same origin; if different, set the full API origin

export async function apiGet<T = any>(path: string): Promise<T | null> {
  try {
    const r = await fetch(BASE + path, { credentials: "include" });
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  }
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T | boolean> {
  try {
    const r = await fetch(BASE + path, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    // Try to parse JSON, fallback to boolean ok
    const ct = r.headers.get("content-type") || "";
    if (ct.includes("application/json")) return await r.json();
    return r.ok;
  } catch {
    return false;
  }
}


export const AuthAPI = {
  whoami: () => apiGet<WhoAmI>("/api/auth/whoami"),
  logout: () => apiPost("/api/auth/logout"),
  login: (email: string, password: string) =>
    apiPost("/api/auth/login", { email, password }),
  register: (payload: Record<string, any>) =>
    apiPost("/api/auth/register", payload),
};

// Trial system removed - not in use