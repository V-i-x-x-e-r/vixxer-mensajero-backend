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


def conversaciones(usuario_id: str, limite: int = 300):
    r = (
        supabase.table("mensajes")
        .select("*")
        .or_(f"remitente_id.eq.{usuario_id},destinatario_id.eq.{usuario_id}")
        .order("enviado_en", desc=True)
        .limit(limite)
        .execute()
    )
    ultimos = {}
    no_leidos = {}
    for m in r.data:
        otro = m["destinatario_id"] if m["remitente_id"] == usuario_id else m["remitente_id"]
        if otro not in ultimos:
            ultimos[otro] = m
        if m["destinatario_id"] == usuario_id and m["leido_en"] is None:
            no_leidos[otro] = no_leidos.get(otro, 0) + 1
    salida = []
    for otro, ultimo in ultimos.items():
        salida.append({
            "otro_id": otro,
            "ultimo_cifrado": ultimo["contenido_cifrado"],
            "ultimo_nonce": ultimo["nonce"],
            "ultimo_remitente_id": ultimo["remitente_id"],
            "enviado_en": ultimo["enviado_en"],
            "no_leidos": no_leidos.get(otro, 0),
        })
    salida.sort(key=lambda c: c["enviado_en"], reverse=True)
    return salida


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
