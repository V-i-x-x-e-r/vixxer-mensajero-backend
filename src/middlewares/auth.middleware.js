// Protege rutas: exige un JWT válido en el header Authorization: Bearer <token>.
// Si es válido, deja el usuario en req.user.
import { ApiError } from './error.middleware.js';
import { verifyToken } from '../utils/jwt.js';

export function requireAuth(req, _res, next) {
  const header = req.headers.authorization || '';
  const [scheme, token] = header.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return next(new ApiError(401, 'Falta el token de autenticación'));
  }

  try {
    const payload = verifyToken(token);
    req.user = { id: payload.sub, username: payload.username };
    next();
  } catch {
    next(new ApiError(401, 'Token inválido o expirado'));
  }
}
