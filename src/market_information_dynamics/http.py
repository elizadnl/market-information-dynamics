from __future__ import annotations


def activate_system_trust_store() -> bool:
    """Use the operating system certificate store when ``truststore`` is available.

    ``requests`` normally relies on its bundled CA set. On managed Windows machines,
    HTTPS traffic may be signed by a root certificate that is trusted by Windows but is
    absent from that bundle. PyPA's ``truststore`` exposes the native OS trust store to
    Python's ``ssl`` module without disabling certificate verification.

    The function is intentionally safe to call more than once and falls back to the
    default Python/requests behaviour if ``truststore`` is not installed.
    """
    try:
        import truststore
    except ImportError:
        return False

    truststore.inject_into_ssl()
    return True
