from pipeline.src import notify


def test_send_alerts_no_alerts():
    result = notify.send_alerts([])
    assert result["sent"] == 0


def test_send_alerts_without_credentials(monkeypatch):
    monkeypatch.setattr(notify, "_load_service_account", lambda: None)
    result = notify.send_alerts([{
        "id": "maiz-buy-2026-11-16",
        "product": "maiz",
        "direction": "buy",
        "tier": "strong",
        "message": "Maíz: nuevo mínimo de 2 años.",
    }])
    assert result["sent"] == 0
    assert "skipped" in result
