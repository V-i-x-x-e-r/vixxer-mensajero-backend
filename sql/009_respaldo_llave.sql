-- Respaldo cifrado de la llave privada. Ejecutar en el SQL Editor de Supabase.
-- El server guarda solo el blob cifrado + salt: no puede descifrarlo (zero-knowledge).

alter table usuarios add column respaldo_cifrado text;
alter table usuarios add column respaldo_nonce text;
alter table usuarios add column respaldo_salt text;
