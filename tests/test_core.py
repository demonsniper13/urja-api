import hashlib
import hmac

from app.normalize import normalize_energy, to_float


def test_number_conversion():
    assert to_float("12.5") == 12.5
    assert to_float("") is None
    assert to_float("bad") is None


def test_energy_delta_and_reset():
    payload = {
        "data": [
            {"timestamp": "23/06/2026 23:30", "kwh": "100", "kvah": "110", "voltR": "230"},
            {"timestamp": "24/06/2026 00:00", "kwh": "101.5", "kvah": "112", "voltR": "231"},
            {"timestamp": "24/06/2026 00:30", "kwh": "2", "kvah": "3", "voltR": "229"},
        ]
    }
    result = normalize_energy(payload)
    assert result[0].consumption_kwh is None
    assert result[1].consumption_kwh == 1.5
    assert result[2].consumption_kwh is None
    assert result[0].timestamp.isoformat().endswith("+05:30")


def test_signing_formula():
    secret = "test-secret"
    message = "GET\n/portal/export\npage=1\n1000"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    assert expected == "9aaf1cb93b2daff7616befe082a8ca2bb98add6ce67da3326c18574192ff8a55"
