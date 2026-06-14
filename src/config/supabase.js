// Cliente de Supabase con la SERVICE_ROLE key.
// ⚠️ Esta key bypassea RLS y NUNCA debe llegar al cliente móvil.
//    Solo vive aquí, en el backend, leída desde .env.
import { createClient } from '@supabase/supabase-js';
import { config } from './env.js';

export const supabase = createClient(
  config.SUPABASE_URL,
  config.SUPABASE_SERVICE_ROLE_KEY,
  {
    auth: { persistSession: false, autoRefreshToken: false },
  },
);
