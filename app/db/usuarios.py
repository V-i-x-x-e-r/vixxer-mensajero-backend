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


def buscar_por_codigo(codigo: str):
    r = supabase.table("usuarios").select("id, usuario, llave_publica").eq("codigo", codigo).limit(1).execute()
    return r.data[0] if r.data else None


def buscar(q: str, excepto_id: str, limite: int = 20):
    r = (
        supabase.table("usuarios")
        .select("id, usuario, llave_publica")
        .ilike("usuario", f"%{q}%")
        .neq("id", excepto_id)
        .limit(limite)
        .execute()
    )
    return r.data
