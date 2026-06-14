import { Router } from 'express';
import { history, remove } from '../controllers/messages.controller.js';
import { requireAuth } from '../middlewares/auth.middleware.js';

const router = Router();

router.get('/:userId', requireAuth, history);
router.delete('/:id', requireAuth, remove);

export default router;
