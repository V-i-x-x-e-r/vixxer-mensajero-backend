// Helpers para firmar y verificar JWT. Un solo lugar que toca la librería.
import jwt from 'jsonwebtoken';
import { config } from '../config/env.js';

export function signToken(payload) {
  return jwt.sign(payload, config.JWT_SECRET, { expiresIn: config.JWT_EXPIRES_IN });
}

export function verifyToken(token) {
  // Lanza si es inválido/expirado; quien llama decide cómo responder.
  return jwt.verify(token, config.JWT_SECRET);
}
