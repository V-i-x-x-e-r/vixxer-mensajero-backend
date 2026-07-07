alter table mensajes_grupo add column if not exists leido_por jsonb default '{}'::jsonb;
