from uuid import UUID


def es_uuid(valor):
    try:
        UUID(str(valor))
        return True
    except (ValueError, TypeError, AttributeError):
        return False
