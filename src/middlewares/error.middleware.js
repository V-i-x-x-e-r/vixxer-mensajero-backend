// Manejador central de errores. Cualquier `next(err)` cae aquí.
// Nunca filtra stack traces ni detalles internos al cliente en producción.
import { logger } from '../config/logger.js';
import { config } from '../config/env.js';

export class ApiError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

// 404 para rutas no encontradas.
export function notFound(req, res) {
  res.status(404).json({ error: 'Ruta no encontrada' });
}

// Handler final (4 args para que Express lo reconozca como error handler).
// eslint-disable-next-line no-unused-vars
export function errorHandler(err, req, res, _next) {
  const status = err.status || 500;

  if (status >= 500) {
    logger.error({ err }, 'Error no controlado');
  }

  res.status(status).json({
    error: status >= 500 && config.isProd ? 'Error interno del servidor' : err.message,
    ...(err.details ? { details: err.details } : {}),
  });
}
