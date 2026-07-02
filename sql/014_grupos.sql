-- Grupos con cifrado E2EE por-miembro (una copia cifrada del mensaje por cada integrante).
-- Ejecutar en el SQL Editor de Supabase.

create table if not exists grupos
(
    id         uuid primary key default gen_random_uuid(),
    nombre     text not null,
    creador_id uuid not null references usuarios(id),
    avatar_url text,
    creado_en  timestamptz default now()
);

create table if not exists grupo_miembros
(
    grupo_id    uuid not null references grupos(id) on delete cascade,
    usuario_id  uuid not null references usuarios(id) on delete cascade,
    agregado_en timestamptz default now(),
    primary key (grupo_id, usuario_id)
);

create table if not exists mensajes_grupo
(
    id           uuid primary key default gen_random_uuid(),
    grupo_id     uuid not null references grupos(id) on delete cascade,
    remitente_id uuid not null references usuarios(id),
    cliente_id   text,
    enviado_en   timestamptz default now()
);

create table if not exists mensajes_grupo_cifrados
(
    mensaje_id        uuid not null references mensajes_grupo(id) on delete cascade,
    destinatario_id   uuid not null references usuarios(id) on delete cascade,
    contenido_cifrado text not null,
    nonce             text not null,
    primary key (mensaje_id, destinatario_id)
);

create index if not exists idx_grupo_miembros_usuario on grupo_miembros (usuario_id);
create index if not exists idx_mensajes_grupo_grupo on mensajes_grupo (grupo_id, enviado_en desc);
create index if not exists idx_mensajes_grupo_cifrados_dest on mensajes_grupo_cifrados (destinatario_id);
create unique index if not exists mensajes_grupo_cliente_id_key on mensajes_grupo (grupo_id, cliente_id) where cliente_id is not null;
