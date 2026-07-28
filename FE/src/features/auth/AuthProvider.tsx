import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi, setAccessToken, userApi } from "../../lib/api";
import type { User } from "../../lib/types";

interface AuthContextValue {
  user: User | null;
  isBootstrapping: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    let active = true;
    authApi
      .restoreSession()
      .then((restoredUser) => {
        if (active) setUser(restoredUser);
      })
      .catch(() => {
        setAccessToken(null);
      })
      .finally(() => {
        if (active) setIsBootstrapping(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    await authApi.login(username, password);
    const restoredUser = await userApi.me();
    setUser(restoredUser);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, isBootstrapping, signIn, signOut, setUser }),
    [user, isBootstrapping, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// This hook intentionally shares the provider's module so its contract remains local.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
