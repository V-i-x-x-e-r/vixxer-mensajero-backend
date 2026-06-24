-- Solicitudes de amistad y bloqueos. Ejecutar en el SQL Editor de Supabase.

create table solicitudes
(
    id        uuid primary key default gen_random_uuid(),
    de_id     uuid references usuarios(id),
    para_id   uuid references usuarios(id),
    estado    text not null default 'pendiente',
    creado_en timestamptz default now(),
    unique (de_id, para_id)
);

create table bloqueos
(
    id           uuid primary key default gen_random_uuid(),
    usuario_id   uuid references usuarios(id),
    bloqueado_id uuid references usuarios(id),
    creado_en    timestamptz default now(),
    unique (usuario_id, bloqueado_id)
);

create index idx_solicitudes_para on public.solicitudes (para_id, estado);
