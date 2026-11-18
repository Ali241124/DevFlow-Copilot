
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.app.api import routes
from backend.app.schemas.context import NormalizedContext


class FakeContextBuilder:

    def build(self, client_text="", image_paths=None):

        image_paths = image_paths or []

        if client_text and image_paths:
            mode = "combined"
        elif client_text:
            mode = "text_only"
        elif image_paths:
            mode = "image_only"
        else:
            raise ValueError(
                "At least client text or one screenshot is required."
            )

        return NormalizedContext(
            client_text=client_text,
            image_paths=image_paths,
            input_mode=mode
        )


@pytest.fixture
def client(monkeypatch, tmp_path):

    monkeypatch.setattr(
        routes,
        "ContextBuilder",
        FakeContextBuilder
    )

    monkeypatch.setattr(
        routes,
        "UPLOAD_DIR",
        tmp_path
    )

    return TestClient(app)


def create_test_image():

    image = Image.new("RGB", (100, 100), color="white")

    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    return image_bytes

def test_text_only_analysis(client):

    response = client.post(
        "/api/v1/requirements/analyze",
        data={
            "client_text": "Build a task management application."
        }
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert result["input_mode"] == "text_only"
    assert result["client_text"] == "Build a task management application."
    assert result["image_paths"] == []


def test_image_only_analysis(client):

    response = client.post(
        "/api/v1/requirements/analyze",
        files={
            "file": (
                "sample.png",
                create_test_image(),
                "image/png"
            )
        }
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert result["input_mode"] == "image_only"
    assert result["client_text"] == ""
    assert len(result["image_paths"]) == 1


def test_combined_analysis(client):

    response = client.post(
        "/api/v1/requirements/analyze",
        data={
            "client_text": "Build a task management application."
        },
        files={
            "file": (
                "sample.png",
                create_test_image(),
                "image/png"
            )
        }
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert result["input_mode"] == "combined"
    assert result["client_text"] != ""
    assert len(result["image_paths"]) == 1


def test_empty_input_rejected(client):

    response = client.post(
        "/api/v1/requirements/analyze"
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "At least client text or one screenshot is required."
    )

def test_unsupported_file_format_rejected(client):

    response = client.post(
        "/api/v1/screenshots/upload",
        files={
            "file": (
                "document.txt",
                BytesIO(b"This is not an image."),
                "text/plain"
            )
        }
    )

    assert response.status_code == 415

    assert "Unsupported image format" in response.json()["detail"]


def test_corrupted_image_rejected(client):

    response = client.post(
        "/api/v1/screenshots/upload",
        files={
            "file": (
                "corrupted.png",
                BytesIO(b"This is not a valid PNG image."),
                "image/png"
            )
        }
    )

    assert response.status_code == 400

    assert "Invalid or corrupted image file" in response.json()["detail"]

def test_oversized_image_rejected(client):

    oversized_content = b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/api/v1/screenshots/upload",
        files={
            "file": (
                "large.png",
                BytesIO(oversized_content),
                "image/png"
            )
        }
    )

    assert response.status_code == 413

    assert "Maximum allowed size is 5 MB" in response.json()["detail"]


def test_image_extension_mismatch_rejected(client):

    image_bytes = create_test_image()

    response = client.post(
        "/api/v1/screenshots/upload",
        files={
            "file": (
                "sample.jpg",
                image_bytes,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 415

    assert "extension does not match" in response.json()["detail"]
