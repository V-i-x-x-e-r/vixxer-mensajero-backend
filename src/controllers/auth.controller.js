// Lógica de registro y login. Implementado y funcional.
import bcrypt from 'bcryptjs';
import { config } from '../config/env.js';
import { ApiError } from '../middlewares/error.middleware.js';
import { signToken } from '../utils/jwt.js';
import * as User from '../models/user.model.js';

export async function register(req, res, next) {
  try {
    const { username, password, publicKey } = req.body;

    const existing = await User.findByUsernameWithHash(username);
    if (existing) {
      throw new ApiError(409, 'Ese nombre de usuario ya está tomado');
    }

    const passwordHash = await bcrypt.hash(password, config.BCRYPT_SALT_ROUNDS);
    const user = await User.createUser({ username, passwordHash, publicKey });

    const token = signToken({ sub: user.id, username: user.username });
    res.status(201).json({ token, user });
  } catch (err) {
    next(err);
  }
}

export async function login(req, res, next) {
  try {
    const { username, password } = req.body;

    const user = await User.findByUsernameWithHash(username);
    // Mismo mensaje genérico exista o no el usuario: no revelamos cuáles existen.
    const ok = user && (await bcrypt.compare(password, user.password_hash));
    if (!ok) {
      throw new ApiError(401, 'Usuario o contraseña incorrectos');
    }

    await User.touchLastSeen(user.id);
    const token = signToken({ sub: user.id, username: user.username });
    res.json({
      token,
      user: { id: user.id, username: user.username, public_key: user.public_key },
    });
  } catch (err) {
    next(err);
  }
}

export async function me(req, res, next) {
  try {
    const user = await User.findById(req.user.id);
    if (!user) throw new ApiError(404, 'Usuario no encontrado');
    res.json({ user });
  } catch (err) {
    next(err);
  }
}
