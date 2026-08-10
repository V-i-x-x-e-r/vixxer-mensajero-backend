-- Baja de cuenta. Ejecutar en el SQL Editor de Supabase ANTES de desplegar el codigo que la usa.
-- Varias llaves foraneas hacia usuarios no tienen ON DELETE CASCADE, asi que un DELETE
-- suelto sobre usuarios falla. Esta funcion borra en orden y dentro de una sola transaccion:
-- o se va todo, o no se va nada.

create or replace function borrar_cuenta(p_usuario uuid)
returns void
language plpgsql
as $$
begin
    update grupos g
       set creador_id = (
           select gm.usuario_id
             from grupo_miembros gm
            where gm.grupo_id = g.id
              and gm.usuario_id <> p_usuario
            order by (gm.rol = 'admin') desc, gm.agregado_en asc
            limit 1
       )
     where g.creador_id = p_usuario
       and exists (
           select 1
             from grupo_miembros gm
            where gm.grupo_id = g.id
              and gm.usuario_id <> p_usuario
       );

    delete from grupos where creador_id = p_usuario;

    delete from mensajes_grupo_cifrados
     where mensaje_id in (select id from mensajes_grupo where remitente_id = p_usuario);

    delete from mensajes_grupo where remitente_id = p_usuario;

    delete from grupo_miembros where usuario_id = p_usuario;

    delete from mensajes where remitente_id = p_usuario or destinatario_id = p_usuario;

    delete from solicitudes where de_id = p_usuario or para_id = p_usuario;

    delete from bloqueos where usuario_id = p_usuario or bloqueado_id = p_usuario;

    delete from limpiezas where usuario_id = p_usuario or otro_id = p_usuario;

    delete from push_tokens where user_id = p_usuario;

    delete from usuarios where id = p_usuario;
end;
$$;
