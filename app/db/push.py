from app.db.supabase import supabase
from app.core.validar import es_uuid


def guardar(user_id: str, token: str, plataforma: str = None):
    if not es_uuid(user_id) or not token:
        return
    try:
        supabase.table("push_tokens").upsert({
            "token": token,
            "user_id": user_id,
            "plataforma": plataforma,
        }).execute()
    except Exception:
        pass


def tokens_de(user_id: str):
    if not es_uuid(user_id):
        return []
    try:
        r = supabase.table("push_tokens").select("token").eq("user_id", user_id).execute()
        return [fila["token"] for fila in r.data]
    except Exception:
        return []


def borrar(token: str):
    if not token:
        return
    try:
        supabase.table("push_tokens").delete().eq("token", token).execute()
    except Exception:
        pass
