from changed_services import services_from_files


def test_detects_services(tmp_path, monkeypatch):
    (tmp_path / "services" / "orders").mkdir(parents=True)
    (tmp_path / "services" / "payments").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    files = [
        "services/orders/orders.py",
        "services/orders/test_orders.py",
        "services/payments/requirements.txt",
        "README.md",
        "app/calc.py",
    ]
    assert services_from_files(files) == ["orders", "payments"]


def test_ignores_deleted_and_top_level(tmp_path, monkeypatch):
    (tmp_path / "services" / "orders").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    files = ["services/legacy/main.py", "services/README.md", "services/orders/x.py"]
    assert services_from_files(files) == ["orders"]


def test_no_changes():
    assert services_from_files(["docs/index.md"]) == []
