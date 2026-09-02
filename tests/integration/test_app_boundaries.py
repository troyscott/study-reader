"""Executable security-boundary and application lifecycle tests."""

from fastapi import APIRouter
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from study_reader.admin.app import create_app as create_admin_app
from study_reader.admin.routes import router as admin_router
from study_reader.config import Settings
from study_reader.reader.app import create_app as create_reader_app
from study_reader.reader.routes import router as reader_router


def router_paths(router: APIRouter) -> set[str]:
    """Return paths declared on an application-owned route table."""

    return {route.path for route in router.routes if isinstance(route, APIRoute)}


def test_reader_lifespan_sets_and_clears_readiness(test_settings: Settings) -> None:
    app = create_reader_app(test_settings)

    assert not hasattr(app.state, "ready")
    with TestClient(app) as client:
        assert app.state.ready is True
        assert app.state.settings is test_settings
        assert client.get("/health").json() == {
            "service": "reader",
            "status": "ok",
        }
    assert app.state.ready is False


def test_public_reader_exposes_only_safe_methods(test_settings: Settings) -> None:
    app = create_reader_app(test_settings)
    disallowed_methods = {"POST", "PUT", "PATCH", "DELETE"}

    exposed_disallowed_methods = {
        method
        for route in reader_router.routes
        if isinstance(route, APIRoute)
        for method in route.methods
        if method in disallowed_methods
    }

    assert exposed_disallowed_methods == set()
    assert not any(path.startswith("/admin") for path in router_paths(reader_router))

    with TestClient(app) as client:
        assert client.post("/").status_code == 405
        assert client.get("/admin/").status_code == 404


def test_reader_and_admin_route_tables_are_separate(test_settings: Settings) -> None:
    reader_paths = router_paths(reader_router)
    admin_paths = router_paths(admin_router)

    assert "/" in reader_paths
    assert "/health" in reader_paths
    assert "/admin/" in admin_paths
    assert "/admin/health" in admin_paths
    assert reader_paths.isdisjoint(admin_paths)

    with TestClient(create_reader_app(test_settings)) as reader_client:
        assert "Study Reader" in reader_client.get("/").text

    with TestClient(create_admin_app(test_settings)) as admin_client:
        assert admin_client.get("/admin/").json() == {
            "service": "admin",
            "status": "foundation",
        }


def test_admin_lifespan_is_exercised(test_settings: Settings) -> None:
    app = create_admin_app(test_settings)

    with TestClient(app) as client:
        response = client.get("/admin/health")

    assert response.status_code == 200
    assert response.json() == {"service": "admin", "status": "ok"}
    assert app.state.ready is False
