from app.db.supabase import supabase


def buscar_solicitud(de_id: str, para_id: str):
    r = (
        supabase.table("solicitudes")
        .select("*")
        .eq("de_id", de_id)
        .eq("para_id", para_id)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


def crear_solicitud(de_id: str, para_id: str):
    r = supabase.table("solicitudes").insert({"de_id": de_id, "para_id": para_id}).execute()
    return r.data[0]


def solicitud_por_id(sid: str):
    r = supabase.table("solicitudes").select("*").eq("id", sid).limit(1).execute()
    return r.data[0] if r.data else None


def actualizar_estado(sid: str, estado: str):
    r = supabase.table("solicitudes").update({"estado": estado}).eq("id", sid).execute()
    return r.data[0] if r.data else None


def pendientes(para_id: str):
    r = (
        supabase.table("solicitudes")
        .select("id, de_id, creado_en")
        .eq("para_id", para_id)
        .eq("estado", "pendiente")
        .order("creado_en")
        .execute()
    )
    return r.data


def ids_amigos(usuario_id: str):
    r = (
        supabase.table("solicitudes")
        .select("de_id, para_id")
        .eq("estado", "aceptada")
        .or_(f"de_id.eq.{usuario_id},para_id.eq.{usuario_id}")
        .execute()
    )
    ids = []
    for s in r.data:
        ids.append(s["para_id"] if s["de_id"] == usuario_id else s["de_id"])
    return ids


def eliminar_amistad(usuario_id: str, otro_id: str):
    filtro = (
        f"and(de_id.eq.{usuario_id},para_id.eq.{otro_id}),"
        f"and(de_id.eq.{otro_id},para_id.eq.{usuario_id})"
    )
    supabase.table("solicitudes").delete().eq("estado", "aceptada").or_(filtro).execute()


def crear_bloqueo(usuario_id: str, bloqueado_id: str):
    r = (
        supabase.table("bloqueos")
        .insert({"usuario_id": usuario_id, "bloqueado_id": bloqueado_id})
        .execute()
    )
    return r.data[0]


def esta_bloqueado(usuario_id: str, bloqueado_id: str):
    r = (
        supabase.table("bloqueos")
        .select("id")
        .eq("usuario_id", usuario_id)
        .eq("bloqueado_id", bloqueado_id)
        .limit(1)
        .execute()
    )
    return bool(r.data)
