// Valida req.body contra un esquema Zod antes de llegar al controlador.
// Uso:  router.post('/login', validate(loginSchema), controller)
import { ApiError } from './error.middleware.js';

export function validate(schema) {
  return (req, _res, next) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      const details = result.error.issues.map((i) => ({
        campo: i.path.join('.'),
        mensaje: i.message,
      }));
      return next(new ApiError(400, 'Datos inválidos', details));
    }
    req.body = result.data; // datos ya parseados y limpios
    next();
  };
}
