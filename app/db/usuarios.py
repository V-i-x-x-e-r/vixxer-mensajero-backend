from app.db.supabase import supabase

def buscar_por_usuario(usuario: str):
    r = supabase.table("usuarios").select("*").eq("usuario", usuario).limit(1).execute()
    return r.data[0] if r.data else None

def buscar_por_id(uid: str):
    r = supabase.table("usuarios").select("*").eq("id", uid).limit(1).execute()
    return r.data[0] if r.data else None

def crear(datos: dict):
    r = supabase.table("usuarios").insert(datos).execute()
    return r.data[0]