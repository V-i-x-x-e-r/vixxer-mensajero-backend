from app.db.supabase import supabase
from app.core.validar import es_uuid


def crear(nombre: str, creador_id: str, miembros: list):
    r = supabase.table("grupos").insert({"nombre": nombre, "creador_id": creador_id}).execute()
    grupo = r.data[0]
    ids = {creador_id}
    for uid in miembros:
        if es_uuid(uid):
            ids.add(uid)
    filas = [{"grupo_id": grupo["id"], "usuario_id": uid} for uid in ids]
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


def miembros_ids(grupo_id: str):
    r = supabase.table("grupo_miembros").select("usuario_id").eq("grupo_id", grupo_id).execute()
    return [x["usuario_id"] for x in r.data]


def salir(grupo_id: str, usuario_id: str):
    if not es_uuid(grupo_id) or not es_uuid(usuario_id):
        return
    supabase.table("grupo_miembros").delete().eq("grupo_id", grupo_id).eq("usuario_id", usuario_id).execute()


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
        }
    return salida


def info(grupo_id: str):
    if not es_uuid(grupo_id):
        return None
    r = supabase.table("grupos").select("*").eq("id", grupo_id).limit(1).execute()
    if not r.data:
        return None
    grupo = r.data[0]
    ids = miembros_ids(grupo_id)
    if ids:
        us = supabase.table("usuarios").select("id, usuario, llave_publica, avatar_url").in_("id", ids).execute()
        grupo["miembros"] = us.data
    else:
        grupo["miembros"] = []
    return grupo


def guardar_mensaje(grupo_id: str, remitente_id: str, cliente_id, cifrados: list):
    if cliente_id:
        previo = (
            supabase.table("mensajes_grupo")
            .select("*")
            .eq("grupo_id", grupo_id)
            .eq("cliente_id", cliente_id)
            .limit(1)
            .execute()
        )
        if previo.data:
            return previo.data[0], False
    r = (
        supabase.table("mensajes_grupo")
        .insert({"grupo_id": grupo_id, "remitente_id": remitente_id, "cliente_id": cliente_id})
        .execute()
    )
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
            "contenido_cifrado": cif["contenido_cifrado"],
            "nonce": cif["nonce"],
        })
    return salida
