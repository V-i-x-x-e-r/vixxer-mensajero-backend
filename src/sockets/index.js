// Socket.IO: tiempo real. Autenticación por JWT en el handshake.
// El servidor reenvía blobs cifrados; jamás los lee.
import { verifyToken } from '../utils/jwt.js';
import { logger } from '../config/logger.js';
import * as Message from '../models/message.model.js';
import * as User from '../models/user.model.js';

// Mapa userId -> Set de socketIds (un usuario puede tener varias sesiones).
const online = new Map();

function addOnline(userId, socketId) {
  if (!online.has(userId)) online.set(userId, new Set());
  online.get(userId).add(socketId);
}
function removeOnline(userId, socketId) {
  const set = online.get(userId);
  if (!set) return;
  set.delete(socketId);
  if (set.size === 0) online.delete(userId);
}

export function registerSocketHandlers(io) {
  // Middleware de autenticación del socket.
  io.use((socket, next) => {
    const token = socket.handshake.auth?.token;
    if (!token) return next(new Error('No autenticado'));
    try {
      const payload = verifyToken(token);
      socket.userId = payload.sub;
      socket.username = payload.username;
      next();
    } catch {
      next(new Error('Token inválido'));
    }
  });

  io.on('connection', (socket) => {
    const { userId } = socket;
    addOnline(userId, socket.id);
    socket.join(`user:${userId}`); // sala personal: facilita enviar a "todas sus sesiones"
    socket.broadcast.emit('user:online', { userId });
    logger.info({ userId }, 'socket conectado');

    // --- Enviar mensaje cifrado ---
    socket.on('message:send', async (payload, ack) => {
      try {
        const { recipientId, encryptedContent, nonce } = payload || {};
        if (!recipientId || !encryptedContent || !nonce) {
          return ack?.({ ok: false, error: 'Payload incompleto' });
        }

        const saved = await Message.saveMessage({
          senderId: userId,
          recipientId,
          encryptedContent,
          nonce,
        });

        // Entregar al destinatario si está conectado (en cualquiera de sus sesiones).
        io.to(`user:${recipientId}`).emit('message:received', {
          messageId: saved.id,
          senderId: userId,
          encryptedContent: saved.encrypted_content,
          nonce: saved.nonce,
          timestamp: saved.created_at,
        });

        if (online.has(recipientId)) {
          await Message.markDelivered(saved.id);
          socket.emit('message:delivered', { messageId: saved.id });
        }

        ack?.({ ok: true, messageId: saved.id, timestamp: saved.created_at });
      } catch (err) {
        logger.error({ err }, 'error en message:send');
        ack?.({ ok: false, error: 'No se pudo enviar' });
      }
    });

    // --- Confirmación de lectura ---
    socket.on('message:read', async ({ messageId, senderId } = {}) => {
      try {
        if (!messageId) return;
        await Message.markRead(messageId, userId);
        if (senderId) {
          io.to(`user:${senderId}`).emit('message:read', { messageId });
        }
      } catch (err) {
        logger.error({ err }, 'error en message:read');
      }
    });

    // --- Indicadores de "escribiendo..." ---
    socket.on('typing:start', ({ recipientId } = {}) => {
      if (recipientId) io.to(`user:${recipientId}`).emit('typing:start', { userId });
    });
    socket.on('typing:stop', ({ recipientId } = {}) => {
      if (recipientId) io.to(`user:${recipientId}`).emit('typing:stop', { userId });
    });

    // --- Desconexión ---
    socket.on('disconnect', async () => {
      removeOnline(userId, socket.id);
      if (!online.has(userId)) {
        // Última sesión cerrada: marcar offline.
        try {
          await User.touchLastSeen(userId);
        } catch (err) {
          logger.error({ err }, 'error al actualizar last_seen');
        }
        socket.broadcast.emit('user:offline', {
          userId,
          lastSeen: new Date().toISOString(),
        });
      }
      logger.info({ userId }, 'socket desconectado');
    });
  });
}
