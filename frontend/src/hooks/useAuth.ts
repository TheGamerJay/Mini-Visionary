import { useEffect, useState } from "react";
import { AuthAPI, WhoAmI } from "../lib/api";

export function useAuth() {
  const [user, setUser] = useState<WhoAmI>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    AuthAPI.whoami().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  async function logout() {
    const ok = await AuthAPI.logout();
    if (ok) setUser(null);
    return ok;
  }

  return { user, setUser, loading, logout };
}