import hashlib
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from ramps.models import RampImage


class RampImageApiTests(APITestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(dir=Path(__file__).resolve().parents[2])
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def upload(self, name="original.png", content=b"unchanged-image-bytes", **fields):
        payload = {
            "kind": "photo",
            "file": SimpleUploadedFile(name, content, content_type="image/png"),
            "caption": "Готовое изделие",
            "color": "beige",
            "has_slats": True,
            "side_rails": False,
            "configuration": '{"height_cm":50,"width_cm":40}',
            **fields,
        }
        return self.client.post("/api/ramp/images/", payload, format="multipart")

    def test_photo_persists_with_original_bytes_and_metadata(self):
        content = b"unchanged-image-bytes"
        response = self.upload(content=content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        stored = RampImage.objects.get(pk=response.data["id"])
        self.assertEqual(stored.original_name, "original.png")
        self.assertEqual(stored.file_sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(stored.configuration, {"height_cm": 50, "width_cm": 40})
        with stored.file.open("rb") as uploaded:
            self.assertEqual(uploaded.read(), content)
        self.assertEqual(self.client.get("/api/ramp/images/?kind=photo").data[0]["id"], stored.id)

    def test_illustration_is_explicitly_marked(self):
        response = self.upload(kind="illustration", image_type="sofa", title="Возле дивана")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_illustration"])

    def test_primary_selection_and_delete_file(self):
        first = self.upload(is_primary=True)
        second = self.upload(name="second.webp", content=b"second", is_primary=True)
        self.assertFalse(RampImage.objects.get(pk=first.data["id"]).is_primary)
        item = RampImage.objects.get(pk=second.data["id"])
        path = item.file.path
        self.assertTrue(Path(path).exists())
        response = self.client.delete(f"/api/ramp/images/{item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Path(path).exists())

    def test_rejects_unsupported_file(self):
        response = self.client.post(
            "/api/ramp/images/",
            {"kind": "photo", "file": SimpleUploadedFile("bad.gif", b"gif", content_type="image/gif")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

