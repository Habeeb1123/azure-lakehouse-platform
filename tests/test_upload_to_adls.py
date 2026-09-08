from pathlib import Path

import pytest

from src.upload_to_adls import upload_layer


class FakeFileClient:
    def __init__(self, remote_path: str):
        self.remote_path = remote_path
        self.uploaded_data = None
        self.overwrite = None

    def upload_data(self, data, overwrite=False):
        self.uploaded_data = data.read()
        self.overwrite = overwrite


class FakeDirectoryClient:
    def create_directory(self):
        return None


class FakeFileSystemClient:
    def __init__(self):
        self.files = {}

    def get_directory_client(self, directory_name: str):
        return FakeDirectoryClient()

    def get_file_client(self, remote_path: str):
        client = FakeFileClient(remote_path)
        self.files[remote_path] = client
        return client


class FakeServiceClient:
    def __init__(self):
        self.file_systems = {}

    def get_file_system_client(self, file_system: str):
        client = FakeFileSystemClient()
        self.file_systems[file_system] = client
        return client


def test_upload_layer_rejects_missing_directory(
    tmp_path: Path,
):
    missing_directory = tmp_path / "missing"

    service_client = FakeServiceClient()

    with pytest.raises(
        FileNotFoundError,
        match="Local directory not found",
    ):
        upload_layer(
            service_client=service_client,
            layer_name="bronze",
            source_directory=missing_directory,
        )


def test_upload_layer_rejects_empty_directory(
    tmp_path: Path,
):
    source_directory = tmp_path / "bronze"
    source_directory.mkdir()

    service_client = FakeServiceClient()

    with pytest.raises(
        FileNotFoundError,
        match="No files found",
    ):
        upload_layer(
            service_client=service_client,
            layer_name="bronze",
            source_directory=source_directory,
        )


def test_upload_layer_uploads_files(
    tmp_path: Path,
):
    source_directory = tmp_path / "gold"
    source_directory.mkdir()

    first_file = (
        source_directory / "fact_orders.parquet"
    )

    second_file = (
        source_directory / "_gold_manifest.json"
    )

    first_file.write_bytes(b"parquet-data")
    second_file.write_bytes(b"manifest-data")

    service_client = FakeServiceClient()

    uploaded_count = upload_layer(
        service_client=service_client,
        layer_name="gold",
        source_directory=source_directory,
    )

    file_system = (
        service_client.file_systems["gold"]
    )

    assert uploaded_count == 2

    assert (
        "olist/fact_orders.parquet"
        in file_system.files
    )

    assert (
        "olist/_gold_manifest.json"
        in file_system.files
    )

    assert (
        file_system.files[
            "olist/fact_orders.parquet"
        ].uploaded_data
        == b"parquet-data"
    )

    assert (
        file_system.files[
            "olist/fact_orders.parquet"
        ].overwrite
        is True
    )