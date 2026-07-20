-- Roles de grupo (admin/miembro) y paridad de mensajes de grupo con el chat 1-a-1.
-- Ejecutar en el SQL Editor de Supabase.

alter table grupo_miembros add column if not exists rol text not null default 'miembro';

update grupo_miembros gm set rol = 'admin' from grupos g
  where g.id = gm.grupo_id and g.creador_id = gm.usuario_id;

alter table mensajes_grupo add column if not exists respuesta_a uuid;
alter table mensajes_grupo add column if not exists reacciones jsonb default '{}'::jsonb;
alter table mensajes_grupo add column if not exists borrado boolean default false;
alter table mensajes_grupo add column if not exists editado boolean default false;
>