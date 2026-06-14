// Búsqueda de usuarios y entrega de claves públicas.
import { ApiError } from '../middlewares/error.middleware.js';
import * as User from '../models/user.model.js';

export async function search(req, res, next) {
  try {
    const q = (req.query.q || '').toString().trim();
    if (q.length < 2) {
      throw new ApiError(400, 'La búsqueda necesita al menos 2 caracteres');
    }
    const results = await User.searchByUsername(q);
    res.json({ results });
  } catch (err) {
    next(err);
  }
}

export async function publicKey(req, res, next) {
  try {
    const user = await User.findById(req.params.id);
    if (!user) throw new ApiError(404, 'Usuario no encontrado');
    res.json({ userId: user.id, username: user.username, publicKey: user.public_key });
  } catch (err) {
    next(err);
  }
}
