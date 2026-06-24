-- Preferencias de privacidad. Ejecutar en el SQL Editor de Supabase.

alter table usuarios add column mostrar_conexion boolean not null default true;
alter table usuarios add column mostrar_acuses boolean not null default true;
