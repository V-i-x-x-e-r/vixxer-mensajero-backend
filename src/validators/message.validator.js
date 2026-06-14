import { z } from 'zod';

// El servidor NO valida el contenido (no puede: está cifrado).
// Solo valida que el sobre tenga la forma correcta.
export const sendMessageSchema = z.object({
  recipientId: z.string().uuid('recipientId debe ser un UUID'),
  encryptedContent: z.string().min(1).max(20000),
  nonce: z.string().min(1).max(512),
});
