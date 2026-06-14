// Acceso a datos de mensajes. El servidor guarda y entrega blobs cifrados.
import { supabase } from '../config/supabase.js';

const FIELDS =
  'id, sender_id, recipient_id, encrypted_content, nonce, created_at, delivered_at, read_at';

export async function saveMessage({ senderId, recipientId, encryptedContent, nonce }) {
  const { data, error } = await supabase
    .from('messages')
    .insert({
      sender_id: senderId,
      recipient_id: recipientId,
      encrypted_content: encryptedContent,
      nonce,
    })
    .select(FIELDS)
    .single();
  if (error) throw error;
  return data;
}

// Conversación 1-a-1 entre dos usuarios, en orden cronológico.
export async function getConversation(userA, userB, limit = 100) {
  const { data, error } = await supabase
    .from('messages')
    .select(FIELDS)
    .or(
      `and(sender_id.eq.${userA},recipient_id.eq.${userB}),and(sender_id.eq.${userB},recipient_id.eq.${userA})`,
    )
    .order('created_at', { ascending: true })
    .limit(limit);
  if (error) throw error;
  return data;
}

export async function markDelivered(messageId) {
  const { error } = await supabase
    .from('messages')
    .update({ delivered_at: new Date().toISOString() })
    .eq('id', messageId)
    .is('delivered_at', null);
  if (error) throw error;
}

export async function markRead(messageId, recipientId) {
  // Solo el destinatario puede marcar como leído.
  const { error } = await supabase
    .from('messages')
    .update({ read_at: new Date().toISOString() })
    .eq('id', messageId)
    .eq('recipient_id', recipientId);
  if (error) throw error;
}

// Borrar un mensaje propio (solo el remitente).
export async function deleteOwnMessage(messageId, senderId) {
  const { data, error } = await supabase
    .from('messages')
    .delete()
    .eq('id', messageId)
    .eq('sender_id', senderId)
    .select('id')
    .maybeSingle();
  if (error) throw error;
  return data; // null si no era suyo / no existía
}
