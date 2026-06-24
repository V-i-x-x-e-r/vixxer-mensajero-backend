from app.db.supabase import supabase


def guardar(datos: dict):
    r = supabase.table("mensajes").insert(datos).execute()
    return r.data[0]


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
