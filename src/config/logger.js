// Logger central (Pino). En dev usa pino-pretty; en prod, JSON estructurado.
import pino from 'pino';
import { config } from './env.js';

export const logger = pino({
  level: config.LOG_LEVEL,
  transport: config.isProd
    ? undefined
    : {
        target: 'pino-pretty',
        options: { colorize: true, translateTime: 'HH:MM:ss' },
      },
});
