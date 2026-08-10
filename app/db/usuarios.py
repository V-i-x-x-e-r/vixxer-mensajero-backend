from datetime import datetime, timezone

from app.db.supabase import supabase
from app.core.validar import es_uuid


def buscar_por_usuario(usuario: str):
    r = supabase.table("usuarios").select("*").eq("usuario", usuario).limit(1).execute()
    return r.data[0] if r.data else None


def buscar_por_id(uid: str):
    r = supabase.table("usuarios").select("*").eq("id", uid).limit(1).execute()
    return r.data[0] if r.data else None


def por_ids(ids: list):
    if not ids:
        return {}
    r = (
        supabase.table("usuarios")
        .select("id, usuario, llave_publica, avatar_url, codigo")
        .in_("id", ids)
        .execute()
    )
    return {u["id"]: u for u in r.data}


def crear(datos: dict):
    r = supabase.table("usuarios").insert(datos).execute()
    return r.data[0]


def actualizar(uid: str, datos: dict):
    r = supabase.table("usuarios").update(datos).eq("id", uid).execute()
    return r.data[0] if r.data else None


def borrar_cuenta(uid: str):
    if not es_uuid(uid):
        return False
    supabase.rpc("borrar_cuenta", {"p_usuario": uid}).execute()
    return True


def borrar_archivos(uid: str):
    if not es_uuid(uid):
        return
    for bucket in ("Media", "Avatares"):
        try:
            objetos = supabase.storage.from_(bucket).list(uid) or []
            rutas = [f"{uid}/{o['name']}" for o in objetos if o.get("name")]
            if rutas:
                supabase.storage.from_(bucket).remove(rutas)
        except Exception:
            continue


def marcar_desconexion(uid: str):
    ahora = datetime.now(timezone.utc).isoformat()
    supabase.table("usuarios").update({"ultima_conexion": ahora}).eq("id", uid).execute()


def buscar_por_codigo(codigo: str):
    r = supabase.table("usuarios").select("id, usuario, llave_publica").eq("codigo", codigo).limit(1).execute()
    return r.data[0] if r.data else None


def nombre_de(uid: str):
    if not es_uuid(uid):
        return "Alguien"
    r = supabase.table("usuarios").select("usuario").eq("id", uid).limit(1).execute()
    return r.data[0]["usuario"] if r.data else "Alguien"


def sin_acuses(ids: list):
    ids = [i for i in ids if es_uuid(i)]
    if not ids:
        return set()
    r = supabase.table("usuarios").select("id, mostrar_acuses").in_("id", ids).execute()
    return {u["id"] for u in r.data if not u.get("mostrar_acuses", True)}
