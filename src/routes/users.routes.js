import { Router } from 'express';
import { search, publicKey } from '../controllers/users.controller.js';
import { requireAuth } from '../middlewares/auth.middleware.js';

const router = Router();

router.get('/search', requireAuth, search);
router.get('/:id/public-key', requireAuth, publicKey);

export default router;
