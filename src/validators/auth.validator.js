import { z } from 'zod';

// username: 3-20 chars, solo letras/números/_/.  (sin PII)
const username = z
  .string()
  .min(3, 'Mínimo 3 caracteres')
  .max(20, 'Máximo 20 caracteres')
  .regex(/^[a-zA-Z0-9_.]+$/, 'Solo letras, números, guión bajo y punto');

const password = z
  .string()
  .min(8, 'Mínimo 8 caracteres')
  .max(128, 'Máximo 128 caracteres');

export const registerSchema = z.object({
  username,
  password,
  // clave pública E2EE generada en el dispositivo (base64). El server solo la guarda.
  publicKey: z.string().min(10, 'publicKey requerida'),
});

export const loginSchema = z.object({
  username,
  password,
});
