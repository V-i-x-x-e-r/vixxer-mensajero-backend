// Acceso a datos de usuarios. Toda query a la tabla `users` vive aquí.
// Los controladores NO hablan con Supabase directo; pasan por el modelo.
import { supabase } from '../config/supabase.js';

const PUBLIC_FIELDS = 'id, username, public_key, last_seen, created_at';

export async function createUser({ username, passwordHash, publicKey }) {
  const { data, error } = await supabase
    .from('users')
    .insert({ username, password_hash: passwordHash, public_key: publicKey })
    .select(PUBLIC_FIELDS)
    .single();
  if (error) throw error;
  return data;
}

// Incluye el hash: SOLO para login. Nunca devolver esto en una respuesta.
export async function findByUsernameWithHash(username) {
  const { data, error } = await supabase
    .from('users')
    .select('id, username, password_hash, public_key')
    .ilike('username', username)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function findById(id) {
  const { data, error } = await supabase
    .from('users')
    .select(PUBLIC_FIELDS)
    .eq('id', id)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function searchByUsername(query, limit = 10) {
  const { data, error } = await supabase
    .from('users')
    .select('id, username, last_seen')
    .ilike('username', `%${query}%`)
    .limit(limit);
  if (error) throw error;
  return data;
}

export async function touchLastSeen(id) {
  const { error } = await supabase
    .from('users')
    .update({ last_seen: new Date().toISOString() })
    .eq('id', id);
  if (error) throw error;
}
