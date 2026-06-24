from datetime import datetime, timezone

from app.db.supabase import supabase


def guardar(datos: dict):
    r = supabase.table("mensajes").insert(datos).execute()
    return r.data[0]


def marcar_entregado(mensaje_id: str):
    ahora = datetime.now(timezone.utc).isoformat()
    r = (
        supabase.table("mensajes")
        .update({"entregado_en": ahora})
        .eq("id", mensaje_id)
        .is_("entregado_en", "null")
        .execute()
    )
    return r.data[0] if r.data else None


def marcar_leido(ids: list):
    if not ids:
        return []
    ahora = datetime.now(timezone.utc).isoformat()
    r = (
        supabase.table("mensajes")
        .update({"leido_en": ahora})
        .in_("id", ids)
        .is_("leido_en", "null")
        .execute()
    )
    return r.data


def conversacion(usuario_a: str, usuario_b: str, limite: int = 50):
    filtro = (
        f"and(remitente_id.eq.{usuario_a},destinatario_id.eq.{usuario_b}),"
        f"and(remitente_id.eq.{usuario_b},destinatario_id.eq.{usuario_a})"
    )
    r = (
        supabase.table("mensajes")
        .select("*")
        .or_(filtro)
        .order("enviado_en")
        .limit(limite)
        .execute()
    )
    return r.data
