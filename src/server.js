// Entry point: HTTP (Express) + WebSocket (Socket.IO) en el mismo puerto.
import { createServer } from 'node:http';
import { Server } from 'socket.io';
import { createApp } from './app.js';
import { config } from './config/env.js';
import { logger } from './config/logger.js';
import { registerSocketHandlers } from './sockets/index.js';

const app = createApp();
const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: {
    origin: config.corsOrigins.length ? config.corsOrigins : false,
    credentials: true,
  },
});

registerSocketHandlers(io);

httpServer.listen(config.PORT, () => {
  logger.info(`🟢 Vixxer backend escuchando en http://localhost:${config.PORT}`);
  logger.info(`   Entorno: ${config.NODE_ENV}`);
});

// Apagado limpio (Railway/Ctrl-C).
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    logger.info(`Recibido ${signal}, cerrando...`);
    io.close();
    httpServer.close(() => process.exit(0));
  });
}
