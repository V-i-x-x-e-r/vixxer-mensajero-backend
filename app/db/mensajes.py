from datetime import datetime, timezone

from app.db.supabase import supabase
from app.core.validar import es_uuid


def guardar(datos: dict):
    cliente_id = datos.get("cliente_id")
    if cliente_id:
        previo = (
            supabase.table("mensajes")
            .select("*")
            .eq("cliente_id", cliente_id)
            .limit(1)
            .execute()
        )
        if previo.data:
            return previo.data[0], False
    r = supabase.table("mensajes").insert(datos).execute()
    return r.data[0], True


def marcar_entregado(mensaje_id: str, destinatario_id: str):
    if not es_uuid(mensaje_id) or not es_uuid(destinatario_id):
        return None
    ahora = datetime.now(timezone.utc).isoformat()
    r = (
        supabase.table("mensajes")
        .update({"entregado_en": ahora})
        .eq("id", mensaje_id)
        .eq("destinatario_id", destinatario_id)
        .is_("entregado_en", "null")
        .execute()
    )
    return r.data[0] if r.data else None


def editar(mensaje_id: str, remitente_id: str, cifrado: str, nonce: str):
    if not es_uuid(mensaje_id) or not es_uuid(remitente_id):
        return None
    r = (
        supabase.table("mensajes")
        .update({"contenido_cifrado": cifrado, "nonce": nonce, "editado": True})
        .eq("id", mensaje_id)
        .eq("remitente_id", remitente_id)
        .execute()
    )
    return r.data[0] if r.data else None


def borrar(mensaje_id: str, remitente_id: str):
    if not es_uuid(mensaje_id) or not es_uuid(remitente_id):
        return None
    r = (
        supabase.table("mensajes")
        .update({"contenido_cifrado": "BORRADO", "nonce": ""})
        .eq("id", mensaje_id)
        .eq("remitente_id", remitente_id)
        .execute()
    )
    return r.data[0] if r.data else None


def marcar_entregados_de(destinatario_id: str):
    ahora = datetime.now(timezone.utc).isoformat()
    r = (
        supabase.table("mensajes")
        .update({"entregado_en": ahora})
        .eq("destinatario_id", destinatario_id)
        .is_("entregado_en", "null")
        .execute()
    )
    return r.data


def marcar_leido(ids: list, lector_id: str):
    ids = [i for i in (ids or []) if es_uuid(i)]
    if not ids or not es_uuid(lector_id):
        return []
    ahora = datetime.now(timezone.utc).isoformat()
    r = (
        supabase.table("mensajes")
        .update({"leido_en": ahora})
        .in_("id", ids)
        .eq("destinatario_id", lector_id)
        .is_("leido_en", "null")
        .execute()
    )
    return r.data


def reaccionar(mensaje_id: str, usuario_id: str, emoji: str):
    if not es_uuid(mensaje_id) or not es_uuid(usuario_id):
        return None
    r = (
        supabase.table("mensajes")
        .select("remitente_id, destinatario_id, reacciones")
        .eq("id", mensaje_id)
        .limit(1)
        .execute()
    )
    if not r.data:
        return None
    fila = r.data[0]
    if usuario_id not in (fila["remitente_id"], fila["destinatario_id"]):
        return None
    reacciones = fila.get("reacciones") or {}
    if reacciones.get(usuario_id) == emoji:
        reacciones.pop(usuario_id, None)
    else:
        reacciones[usuario_id] = emoji
    u = (
        supabase.table("mensajes")
        .update({"reacciones": reacciones})
        .eq("id", mensaje_id)
        .execute()
    )
    return u.data[0] if u.data else None


def limpiar_conversacion(usuario_id: str, otro_id: str):
    if not es_uuid(usuario_id) or not es_uuid(otro_id):
        return
    ahora = datetime.now(timezone.utc).isoformat()
    supabase.table("limpiezas").upsert(
        {"usuario_id": usuario_id, "otro_id": otro_id, "limpiado_en": ahora},
        on_conflict="usuario_id,otro_id",
    ).execute()


def _limpiezas_de(usuario_id: str):
    r = (
        supabase.table("limpiezas")
        .select("otro_id, limpiado_en")
        .eq("usuario_id", usuario_id)
        .execute()
    )
    return {x["otro_id"]: x["limpiado_en"] for x in r.data}


def conversaciones(usuario_id: str, limite: int = 300):
    if not es_uuid(usuario_id):
        return []
    r = (
        supabase.table("mensajes")
        .select("*")
        .or_(f"remitente_id.eq.{usuario_id},destinatario_id.eq.{usuario_id}")
        .order("enviado_en", desc=True)
        .limit(limite)
        .execute()
    )
    cortes = _limpiezas_de(usuario_id)
    ultimos = {}
    no_leidos = {}
    for m in r.data:
        otro = m["destinatario_id"] if m["remitente_id"] == usuario_id else m["remitente_id"]
        corte = cortes.get(otro)
        if corte and m["enviado_en"] <= corte:
            continue
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


def conversacion(usuario_a: str, usuario_b: str, limite: int = 50, antes: str = None):
    if not es_uuid(usuario_a) or not es_uuid(usuario_b):
        return []
    filtro = (
        f"and(remitente_id.eq.{usuario_a},destinatario_id.eq.{usuario_b}),"
        f"and(remitente_id.eq.{usuario_b},destinatario_id.eq.{usuario_a})"
    )
    consulta = (
        supabase.table("mensajes")
        .select("*")
        .or_(filtro)
        .order("enviado_en", desc=True)
        .limit(limite)
    )
    if antes:
        consulta = consulta.lt("enviado_en", antes)
    r = consulta.execute()
    filas = list(reversed(r.data))
    corte = _limpiezas_de(usuario_a).get(usuario_b)
    if corte:
        return [m for m in filas if m["enviado_en"] > corte]
    return filas
