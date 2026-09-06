import { createClient, SupabaseClient, User, Session, AuthChangeEvent } from "@supabase/supabase-js";

let supabaseInstance: SupabaseClient | null = null;
let initPromise: Promise<SupabaseClient | null> | null = null;

// Pre-configured evaluator user for 1-click judging demo
export const EVALUATOR_USER: User = {
  id: "00000000-0000-0000-0000-000000000001",
  app_metadata: { provider: "email" },
  user_metadata: {
    display_name: "Lead Hackathon Evaluator",
    role: "judge",
  },
  aud: "authenticated",
  confirmation_sent_at: new Date().toISOString(),
  recovery_sent_at: undefined,
  email_change_sent_at: undefined,
  new_email: undefined,
  invited_at: undefined,
  action_link: undefined,
  email: "judge@reco.ai",
  phone: "",
  created_at: new Date().toISOString(),
  confirmed_at: new Date().toISOString(),
  email_confirmed_at: new Date().toISOString(),
  phone_confirmed_at: undefined,
  last_sign_in_at: new Date().toISOString(),
  role: "authenticated",
  updated_at: new Date().toISOString(),
  identities: [],
  is_anonymous: false,
};

export const EVALUATOR_SESSION: Session = {
  access_token: "evaluator_demo_jwt_token_reco_judge",
  token_type: "bearer",
  expires_in: 86400,
  refresh_token: "evaluator_demo_refresh_token",
  user: EVALUATOR_USER,
  expires_at: Math.floor(Date.now() / 1000) + 86400,
};

const EVALUATOR_STORAGE_KEY = "reco_evaluator_session";
type AuthListener = (event: AuthChangeEvent, session: Session | null) => void;
const customListeners = new Set<AuthListener>();

function notifyCustomListeners(event: AuthChangeEvent, session: Session | null) {
  customListeners.forEach((listener) => {
    try {
      listener(event, session);
    } catch (e) {
      console.error("Auth listener error:", e);
    }
  });
}

/**
 * Initialize or retrieve the Supabase client.
 * Fetches runtime config from /api/config or falls back to environment variables.
 */
export async function getSupabaseClient(): Promise<SupabaseClient | null> {
  if (supabaseInstance) return supabaseInstance;

  if (initPromise) return initPromise;

  initPromise = (async () => {
    let url: string | undefined;
    let anonKey: string | undefined;

    if (typeof import.meta !== "undefined" && import.meta.env) {
      url = import.meta.env.VITE_SUPABASE_URL || import.meta.env.SUPABASE_URL;
      anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.SUPABASE_ANON_KEY;
    }

    if (!url || !anonKey) {
      try {
        const configUrl =
          typeof window !== "undefined" && window.location?.origin && window.location.origin !== "null"
            ? `${window.location.origin}/api/config`
            : "http://127.0.0.1:8000/api/config";
        const res = await fetch(configUrl);
        if (res.ok) {
          const config = await res.json();
          if (config.supabase_url && config.supabase_anon_key) {
            url = config.supabase_url;
            anonKey = config.supabase_anon_key;
          }
        }
      } catch (err) {
        console.warn("Could not fetch /api/config for Supabase client:", err);
      }
    }

    if (!url || !anonKey) {
      return null;
    }

    try {
      supabaseInstance = createClient(url, anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      });
      return supabaseInstance;
    } catch (err) {
      console.error("Failed to initialize Supabase client:", err);
      return null;
    }
  })();

  return initPromise;
}

/**
 * Sign in with email and password.
 */
export async function signInWithPassword(email: string, password: string): Promise<{ data: { user: User | null; session: Session | null }; error: Error | null }> {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(EVALUATOR_STORAGE_KEY);
  }

  const client = await getSupabaseClient();
  if (!client) {
    return {
      data: { user: null, session: null },
      error: new Error("Supabase cloud persistence is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY, or use Judge Demo Sign In."),
    };
  }

  const { data, error } = await client.auth.signInWithPassword({ email, password });
  return {
    data: { user: data.user, session: data.session },
    error: error ? new Error(error.message) : null,
  };
}

/**
 * Sign up a new user with email and password.
 */
export async function signUp(
  email: string,
  password: string,
  displayName?: string
): Promise<{ data: { user: User | null; session: Session | null }; error: Error | null }> {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(EVALUATOR_STORAGE_KEY);
  }

  const client = await getSupabaseClient();
  if (!client) {
    return {
      data: { user: null, session: null },
      error: new Error("Supabase cloud persistence is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY, or use Judge Demo Sign In."),
    };
  }

  const { data, error } = await client.auth.signUp({
    email,
    password,
    options: {
      data: {
        display_name: displayName || email.split("@")[0],
      },
    },
  });

  return {
    data: { user: data.user, session: data.session },
    error: error ? new Error(error.message) : null,
  };
}

/**
 * Sign in as pre-configured Evaluator/Judge (1-click demo).
 */
export function signInAsEvaluator(): { user: User; session: Session } {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(EVALUATOR_STORAGE_KEY, JSON.stringify(EVALUATOR_SESSION));
  }
  notifyCustomListeners("SIGNED_IN", EVALUATOR_SESSION);
  return { user: EVALUATOR_USER, session: EVALUATOR_SESSION };
}

/**
 * Sign out current user.
 */
export async function signOut(): Promise<{ error: Error | null }> {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(EVALUATOR_STORAGE_KEY);
  }

  notifyCustomListeners("SIGNED_OUT", null);

  const client = await getSupabaseClient();
  if (client) {
    const { error } = await client.auth.signOut();
    return { error: error ? new Error(error.message) : null };
  }

  return { error: null };
}

/**
 * Get the current active session.
 */
export async function getSession(): Promise<{ session: Session | null; user: User | null }> {
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem(EVALUATOR_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as Session;
        return { session: parsed, user: parsed.user };
      } catch {
        localStorage.removeItem(EVALUATOR_STORAGE_KEY);
      }
    }
  }

  const client = await getSupabaseClient();
  if (!client) {
    return { session: null, user: null };
  }

  const { data } = await client.auth.getSession();
  return { session: data.session, user: data.session?.user || null };
}

/**
 * Listen to auth state changes.
 */
export function onAuthStateChange(
  callback: (event: AuthChangeEvent, session: Session | null) => void
): { data: { subscription: { unsubscribe: () => void } } } {
  customListeners.add(callback);

  let supabaseSubscription: { unsubscribe: () => void } | null = null;

  getSupabaseClient().then((client) => {
    if (client) {
      const { data } = client.auth.onAuthStateChange((event, session) => {
        if (typeof localStorage !== "undefined" && localStorage.getItem(EVALUATOR_STORAGE_KEY)) {
          return;
        }
        callback(event, session);
      });
      supabaseSubscription = data.subscription;
    }
  });

  return {
    data: {
      subscription: {
        unsubscribe: () => {
          customListeners.delete(callback);
          supabaseSubscription?.unsubscribe();
        },
      },
    },
  };
}
