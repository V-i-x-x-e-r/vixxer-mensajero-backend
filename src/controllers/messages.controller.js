// Historial y borrado de mensajes (vía REST). El envío en tiempo real va por Socket.IO.
import { ApiError } from '../middlewares/error.middleware.js';
import * as Message from '../models/message.model.js';

export async function history(req, res, next) {
  try {
    const messages = await Message.getConversation(req.user.id, req.params.userId);
    res.json({ messages });
  } catch (err) {
    next(err);
  }
}

export async function remove(req, res, next) {
  try {
    const deleted = await Message.deleteOwnMessage(req.params.id, req.user.id);
    if (!deleted) throw new ApiError(404, 'Mensaje no encontrado o no es tuyo');
    res.json({ deleted: deleted.id });
  } catch (err) {
    next(err);
  }
}
