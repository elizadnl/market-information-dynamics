from __future__ import annotations

from market_information_dynamics.http import activate_system_trust_store


def test_system_trust_store_activation_is_safe():
    # The dependency is installed in normal project environments. The helper is also
    # intentionally safe when imported in minimal environments.
    result = activate_system_trust_store()
    assert isinstance(result, bool)
