-- Foto de perfil. Ejecutar en el SQL Editor de Supabase.
-- Requiere un bucket de Storage publico llamado "avatares".

alter table usuarios add column avatar_url text;
