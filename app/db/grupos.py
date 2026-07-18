from datetime import datetime, timezone

from postgrest.exceptions import APIError

from app.db.supabase import supabase
from app.core.validar import es_uuid


def crear(nombre: str, creador_id: str, miembros: list):
    r = supabase.table("grupos").insert({"nombre": nombre, "creador_id": creador_id}).execute()
    grupo = r.data[0]
    filas = [{"grupo_id": grupo["id"], "usuario_id": creador_id, "rol": "admin"}]
    for uid in miembros:
        if es_uuid(uid) and uid != creador_id:
            filas.append({"grupo_id": grupo["id"], "usuario_id": uid, "rol": "miembro"})
    supabase.table("grupo_miembros").insert(filas).execute()
    return grupo


def es_miembro(grupo_id: str, usuario_id: str) -> bool:
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return False
    r = (
        supabase.table("grupo_miembros")
        .select("usuario_id")
        .eq("grupo_id", grupo_id)
        .eq("usuario_id", usuario_id)
        .limit(1)
        .execute()
    )
    return bool(r.data)


def es_admin(grupo_id: str, usuario_id: str) -> bool:
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return False
    r = (
        supabase.table("grupo_miembros")
        .select("rol")
        .eq("grupo_id", grupo_id)
        .eq("usuario_id", usuario_id)
        .limit(1)
        .execute()
    )
    return bool(r.data) and r.data[0].get("rol") == "admin"


def miembros_ids(grupo_id: str):
    r = supabase.table("grupo_miembros").select("usuario_id").eq("grupo_id", grupo_id).execute()
    return [x["usuario_id"] for x in r.data]


def agregar_miembros(grupo_id: str, ids: list):
    actuales = set(miembros_ids(grupo_id))
    filas = [
        {"grupo_id": grupo_id, "usuario_id": uid, "rol": "miembro"}
        for uid in ids
        if es_uuid(uid) and uid not in actuales
    ]
    if filas:
        supabase.table("grupo_miembros").insert(filas).execute()
    return [f["usuario_id"] for f in filas]


def quitar_miembro(grupo_id: str, usuario_id: str):
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return
    supabase.table("grupo_miembros").delete().eq("grupo_id", grupo_id).eq("usuario_id", usuario_id).execute()


def cambiar_rol(grupo_id: str, usuario_id: str, rol: str):
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return
    supabase.table("grupo_miembros").update({"rol": rol}).eq("grupo_id", grupo_id).eq("usuario_id", usuario_id).execute()


def actualizar(grupo_id: str, datos: dict):
    r = supabase.table("grupos").update(datos).eq("id", grupo_id).execute()
    return r.data[0] if r.data else None


def salir(grupo_id: str, usuario_id: str):
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return
    quitar_miembro(grupo_id, usuario_id)
    g = supabase.table("grupos").select("creador_id").eq("id", grupo_id).limit(1).execute()
    if not g.data:
        return
    restantes = (
        supabase.table("grupo_miembros")
        .select("usuario_id, rol, agregado_en")
        .eq("grupo_id", grupo_id)
        .order("agregado_en")
        .execute()
    )
    if not restantes.data:
        supabase.table("grupos").delete().eq("id", grupo_id).execute()
        return
    if g.data[0]["creador_id"] != usuario_id:
        return
    admins = [m for m in restantes.data if m.get("rol") == "admin"]
    heredero = (admins or restantes.data)[0]["usuario_id"]
    supabase.table("grupos").update({"creador_id": heredero}).eq("id", grupo_id).execute()
    cambiar_rol(grupo_id, heredero, "admin")


def grupos_de(usuario_id: str):
    if not es_uuid(usuario_id):
        return []
    r = supabase.table("grupo_miembros").select("grupo_id").eq("usuario_id", usuario_id).execute()
    ids = [x["grupo_id"] for x in r.data]
    if not ids:
        return []
    g = supabase.table("grupos").select("*").in_("id", ids).execute()
    conteos = {}
    m = supabase.table("grupo_miembros").select("grupo_id").in_("grupo_id", ids).execute()
    for x in m.data:
        conteos[x["grupo_id"]] = conteos.get(x["grupo_id"], 0) + 1
    ultimos = _ultimos_mensajes(ids, usuario_id)
    salida = []
    for grupo in g.data:
        salida.append({**grupo, "miembros": conteos.get(grupo["id"], 0), "ultimo": ultimos.get(grupo["id"])})
    salida.sort(key=lambda x: (x["ultimo"]["enviado_en"] if x["ultimo"] else x.get("creado_en")) or "", reverse=True)
    return salida


def _ultimos_mensajes(grupo_ids: list, usuario_id: str):
    msgs = (
        supabase.table("mensajes_grupo")
        .select("*")
        .in_("grupo_id", grupo_ids)
        .order("enviado_en", desc=True)
        .limit(200)
        .execute()
    )
    ultimos = {}
    for msg in msgs.data:
        if msg["grupo_id"] not in ultimos:
            ultimos[msg["grupo_id"]] = msg
    if not ultimos:
        return {}
    cif = (
        supabase.table("mensajes_grupo_cifrados")
        .select("*")
        .in_("mensaje_id", [msg["id"] for msg in ultimos.values()])
        .eq("destinatario_id", usuario_id)
        .execute()
    )
    cifrados = {x["mensaje_id"]: x for x in cif.data}
    rem_ids = list({msg["remitente_id"] for msg in ultimos.values()})
    us = supabase.table("usuarios").select("id, usuario, llave_publica").in_("id", rem_ids).execute()
    remitentes = {u["id"]: u for u in us.data}
    salida = {}
    for grupo_id, msg in ultimos.items():
        c = cifrados.get(msg["id"])
        rem = remitentes.get(msg["remitente_id"])
        if not c or not rem:
            continue
        salida[grupo_id] = {
            "enviado_en": msg["enviado_en"],
            "remitente_id": msg["remitente_id"],
            "remitente": rem["usuario"],
            "llave_publica": rem["llave_publica"],
            "contenido_cifrado": c["contenido_cifrado"],
            "nonce": c["nonce"],
            "borrado": msg.get("borrado", False),
        }
    return salida


def info(grupo_id: str):
    if not es_uuid(grupo_id):
        return None
    r = supabase.table("grupos").select("*").eq("id", grupo_id).limit(1).execute()
    if not r.data:
        return None
    grupo = r.data[0]
    filas = (
        supabase.table("grupo_miembros")
        .select("usuario_id, rol, agregado_en")
        .eq("grupo_id", grupo_id)
        .order("agregado_en")
        .execute()
    )
    roles = {x["usuario_id"]: x.get("rol", "miembro") for x in filas.data}
    ids = list(roles.keys())
    grupo["miembros"] = []
    if ids:
        us = supabase.table("usuarios").select("id, usuario, llave_publica, avatar_url").in_("id", ids).execute()
        por_id = {u["id"]: u for u in us.data}
        for x in filas.data:
            u = por_id.get(x["usuario_id"])
            if u:
                grupo["miembros"].append({**u, "rol": roles[u["id"]]})
    return grupo


def guardar_mensaje(grupo_id: str, remitente_id: str, cliente_id, cifrados: list, respuesta_a=None):
    if cliente_id:
        previo = buscar_mensaje_por_cliente(grupo_id, remitente_id, cliente_id)
        if previo:
            return previo, False
    datos = {
        "grupo_id": grupo_id,
        "remitente_id": remitente_id,
        "cliente_id": cliente_id,
        "respuesta_a": respuesta_a if es_uuid(respuesta_a) else None,
    }
    try:
        r = supabase.table("mensajes_grupo").insert(datos).execute()
    except APIError as error:
        if error.code != "23505" or not cliente_id:
            raise
        previo = buscar_mensaje_por_cliente(grupo_id, remitente_id, cliente_id)
        if previo is None:
            raise
        return previo, False
    msg = r.data[0]
    filas = [
        {
            "mensaje_id": msg["id"],
            "destinatario_id": c.get("destinatario_id"),
            "contenido_cifrado": c.get("contenido_cifrado"),
            "nonce": c.get("nonce"),
        }
        for c in cifrados
        if es_uuid(c.get("destinatario_id"))
    ]
    if filas:
        supabase.table("mensajes_grupo_cifrados").insert(filas).execute()
    return msg, True


def buscar_mensaje_por_cliente(grupo_id: str, remitente_id: str, cliente_id: str):
    previo = (
        supabase.table("mensajes_grupo")
        .select("*")
        .eq("grupo_id", grupo_id)
        .eq("remitente_id", remitente_id)
        .eq("cliente_id", cliente_id)
        .limit(1)
        .execute()
    )
    return previo.data[0] if previo.data else None


def mensaje_por_id(mensaje_id: str):
    if not es_uuid(mensaje_id):
        return None
    r = supabase.table("mensajes_grupo").select("*").eq("id", mensaje_id).limit(1).execute()
    return r.data[0] if r.data else None


def reaccionar(mensaje_id: str, usuario_id: str, emoji: str):
    fila = mensaje_por_id(mensaje_id)
    if not fila:
        return None
    reacciones = fila.get("reacciones") or {}
    if reacciones.get(usuario_id) == emoji:
        reacciones.pop(usuario_id, None)
    else:
        reacciones[usuario_id] = emoji
    u = supabase.table("mensajes_grupo").update({"reacciones": reacciones}).eq("id", mensaje_id).execute()
    return u.data[0] if u.data else None


def borrar_mensaje(mensaje_id: str, remitente_id: str):
    if not es_uuid(mensaje_id) or not es_uuid(remitente_id):
        return None
    r = (
        supabase.table("mensajes_grupo")
        .update({"borrado": True})
        .eq("id", mensaje_id)
        .eq("remitente_id", remitente_id)
        .execute()
    )
    return r.data[0] if r.data else None


def editar_mensaje(mensaje_id: str, remitente_id: str, cifrados: list):
    fila = mensaje_por_id(mensaje_id)
    if not fila or fila["remitente_id"] != remitente_id or fila.get("borrado"):
        return None
    filas = [
        {
            "mensaje_id": mensaje_id,
            "destinatario_id": c.get("destinatario_id"),
            "contenido_cifrado": c.get("contenido_cifrado"),
            "nonce": c.get("nonce"),
        }
        for c in cifrados
        if es_uuid(c.get("destinatario_id"))
    ]
    if not filas:
        return None
    supabase.table("mensajes_grupo_cifrados").delete().eq("mensaje_id", mensaje_id).execute()
    supabase.table("mensajes_grupo_cifrados").insert(filas).execute()
    r = supabase.table("mensajes_grupo").update({"editado": True}).eq("id", mensaje_id).execute()
    return r.data[0] if r.data else None


def marcar_leidos(grupo_id: str, usuario_id: str, ids: list):
    validos = [i for i in ids if es_uuid(i)]
    if not validos:
        return []
    r = (
        supabase.table("mensajes_grupo")
        .select("id, remitente_id, leido_por")
        .eq("grupo_id", grupo_id)
        .in_("id", validos)
        .execute()
    )
    ahora = datetime.now(timezone.utc).isoformat()
    cambios = []
    for fila in r.data:
        if fila["remitente_id"] == usuario_id:
            continue
        leido_por = fila.get("leido_por") or {}
        if usuario_id in leido_por:
            continue
        leido_por[usuario_id] = ahora
        supabase.table("mensajes_grupo").update({"leido_por": leido_por}).eq("id", fila["id"]).execute()
        cambios.append({"id": fila["id"], "leido_por": leido_por})
    return cambios


def historial(grupo_id: str, usuario_id: str, antes: str = None, limite: int = 50):
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return []
    consulta = (
        supabase.table("mensajes_grupo")
        .select("*")
        .eq("grupo_id", grupo_id)
        .order("enviado_en", desc=True)
        .limit(limite)
    )
    if antes:
        consulta = consulta.lt("enviado_en", antes)
    r = consulta.execute()
    msgs = list(reversed(r.data))
    if not msgs:
        return []
    ids = [m["id"] for m in msgs]
    c = (
        supabase.table("mensajes_grupo_cifrados")
        .select("*")
        .in_("mensaje_id", ids)
        .eq("destinatario_id", usuario_id)
        .execute()
    )
    cifrados = {x["mensaje_id"]: x for x in c.data}
    salida = []
    for m in msgs:
        cif = cifrados.get(m["id"])
        if not cif:
            continue
        salida.append({
            "id": m["id"],
            "grupo_id": m["grupo_id"],
            "remitente_id": m["remitente_id"],
            "cliente_id": m.get("cliente_id"),
            "enviado_en": m["enviado_en"],
            "respuesta_a": m.get("respuesta_a"),
            "reacciones": m.get("reacciones") or {},
            "borrado": m.get("borrado", False),
            "editado": m.get("editado", False),
            "leido_por": m.get("leido_por") or {},
            "contenido_cifrado": cif["contenido_cifrado"],
            "nonce": cif["nonce"],
        })
    return salida
