from pathlib import Path
import argparse

from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import ResourceExistsError


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LAYER_DIRECTORIES = {
    "bronze": PROJECT_ROOT / "data" / "bronze" / "olist",
    "silver": PROJECT_ROOT / "data" / "silver" / "olist",
    "gold": PROJECT_ROOT / "data" / "gold" / "olist",
}


def create_service_client(
    storage_account_name: str,
) -> DataLakeServiceClient:
    """Create an ADLS Gen2 client using the current Azure CLI login."""

    account_url = (
        f"https://{storage_account_name}.dfs.core.windows.net"
    )

    credential = AzureCliCredential()

    return DataLakeServiceClient(
        account_url=account_url,
        credential=credential,
    )


def ensure_directory(
    file_system_client,
    directory_name: str,
) -> None:
    """Create an ADLS directory if it does not already exist."""

    directory_client = (
        file_system_client.get_directory_client(
            directory_name
        )
    )

    try:
        directory_client.create_directory()
    except ResourceExistsError:
        pass


def upload_layer(
    service_client: DataLakeServiceClient,
    layer_name: str,
    source_directory: Path,
) -> int:
    """Upload one local medallion layer to ADLS Gen2."""

    if not source_directory.exists():
        raise FileNotFoundError(
            f"Local directory not found: {source_directory}"
        )

    file_system_client = (
        service_client.get_file_system_client(
            file_system=layer_name
        )
    )

    ensure_directory(
        file_system_client=file_system_client,
        directory_name="olist",
    )

    local_files = sorted(
        path
        for path in source_directory.iterdir()
        if path.is_file()
    )

    if not local_files:
        raise FileNotFoundError(
            f"No files found in {source_directory}"
        )

    uploaded_count = 0

    for local_path in local_files:
        remote_path = f"olist/{local_path.name}"

        file_client = (
            file_system_client.get_file_client(
                remote_path
            )
        )

        print(
            f"Uploading {layer_name}: "
            f"{local_path.name}"
        )

        with local_path.open("rb") as file:
            file_client.upload_data(
                file,
                overwrite=True,
            )

        uploaded_count += 1

    print(
        f"SUCCESS: {layer_name} "
        f"({uploaded_count} files uploaded)"
    )

    return uploaded_count


def main() -> None:
    """Upload Bronze, Silver and Gold Olist data to ADLS Gen2."""

    parser = argparse.ArgumentParser(
        description=(
            "Upload local Olist medallion data "
            "to Azure Data Lake Storage Gen2."
        )
    )

    parser.add_argument(
        "--storage-account",
        required=True,
        help="Azure Storage account name.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("OLIST ADLS GEN2 UPLOAD")
    print("=" * 70)

    service_client = create_service_client(
        storage_account_name=args.storage_account
    )

    total_files = 0

    for layer_name, source_directory in (
        LAYER_DIRECTORIES.items()
    ):
        total_files += upload_layer(
            service_client=service_client,
            layer_name=layer_name,
            source_directory=source_directory,
        )

    print("=" * 70)
    print(f"Total files uploaded: {total_files}")
    print("ADLS GEN2 UPLOAD COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()