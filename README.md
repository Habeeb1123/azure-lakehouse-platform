# Olist Azure Lakehouse Platform

An end-to-end Azure lakehouse data engineering project built using the Brazilian Olist e-commerce dataset. The platform demonstrates data ingestion, transformation, analytical modelling, automated data quality checks, testing, infrastructure deployment and integration with Azure Data Lake Storage Gen2.

## 1. Project Overview

This project implements a Bronze–Silver–Gold lakehouse architecture to process raw e-commerce data into structured analytical datasets.

The solution combines Python-based data processing with Azure cloud infrastructure. It includes automated ingestion, data cleaning, Gold-layer dimensional modelling, quality validation and storage in Azure Data Lake Storage Gen2.

## 2. Architecture

The platform follows a medallion architecture:

```text
                  OLIST SOURCE DATA
                         |
                         v
                BRONZE DATA LAYER
             Raw CSV data converted
                  into Parquet
                         |
                         v
                 SILVER DATA LAYER
             Cleaned and transformed
                  Parquet datasets
                         |
                         v
                  GOLD DATA LAYER
             Analytical fact and
                 dimension tables
                         |
                         v
              DATA QUALITY CHECKS
              Automated validation
                         |
                         v
               AZURE DATA LAKE
                   STORAGE
```

### Bronze Layer

The Bronze layer ingests the original Olist datasets and converts CSV files into Parquet format.

It contains nine datasets:

* Customers
* Geolocation
* Orders
* Order items
* Order payments
* Order reviews
* Products
* Sellers
* Product category translation

An ingestion manifest records information about the ingestion process.

### Silver Layer

The Silver layer applies data transformation and cleaning.

Key activities include:

* Reading Bronze Parquet datasets.
* Cleaning and standardising data.
* Removing duplicate geolocation records.
* Preparing structured datasets for analytical modelling.
* Generating a transformation manifest.

The geolocation dataset was reduced from 1,000,163 records to 738,332 records after deduplication.

### Gold Layer

The Gold layer contains analytical fact and dimension tables.

| Dataset          |    Rows |
| ---------------- | ------: |
| fact_orders      |  99,441 |
| fact_order_items | 112,650 |
| dim_customers    |  99,441 |
| dim_products     |  32,951 |
| dim_sellers      |   3,095 |
| dim_date         |     774 |

The Gold layer also includes a manifest and a data quality report.

## 3. Technology Stack

| Technology                   | Purpose                              |
| ---------------------------- | ------------------------------------ |
| Python                       | Data ingestion and transformation    |
| Pandas                       | Data processing                      |
| PyArrow                      | Parquet file handling                |
| Pytest                       | Automated testing                    |
| Azure Data Lake Storage Gen2 | Cloud data storage                   |
| Azure Data Factory           | Bronze data validation orchestration |
| Azure CLI                    | Azure resource management            |
| Azure Bicep                  | Infrastructure as Code               |
| Git and GitHub               | Version control                      |

## 4. Data Quality and Testing

The project includes automated Gold-layer data quality checks.

The checks cover:

* Duplicate primary keys.
* Null values in mandatory fields.
* Broken foreign key relationships.
* Incorrect order-item line totals.
* General validation of Gold analytical datasets.

The quality checks are implemented in:

```text
src/quality/gold_quality_checks.py
```

The corresponding tests are in:

```text
tests/test_gold_quality_checks.py
```

The Gold quality report is generated at:

```text
data/gold/olist/_gold_quality_report.json
```

### Automated Test Results

The complete test suite currently contains 24 tests.

**Latest verified result:**

```text
24 passed
```

The five dedicated Gold quality tests validate successful checks and the detection of deliberately introduced data quality issues.

## 5. Pipeline Orchestration

The Python orchestration script coordinates the complete workflow.

File:

```text
src/run_pipeline.py
```

Execution order:

1. Bronze ingestion.
2. Silver transformation.
3. Gold analytical modelling.
4. Automated testing.
5. Upload to Azure Data Lake Storage Gen2.

### Run the Complete Pipeline

From the project root, execute:

```cmd
python src\run_pipeline.py --storage-account stolistgyugu6xvyllq4
```

The orchestration script runs the processing stages and uploads the resulting datasets to Azure.

## 6. Azure Data Lake Storage Gen2

The project uses Azure Data Lake Storage Gen2 for cloud storage.

**Configuration:**

| Setting         | Value                  |
| --------------- | ---------------------- |
| Resource group  | rg-olist-lakehouse-dev |
| Azure region    | francecentral          |
| Storage account | stolistgyugu6xvyllq4   |
| Data Factory    | adfolistgyugu6xvyllq4  |
| Containers      | bronze, silver, gold   |

The storage containers are organised by data layer.

```text
bronze/
  olist/

silver/
  olist/

gold/
  olist/
```

The Azure Data Factory managed identity has been assigned the Storage Blob Data Contributor role to support access to the storage account.

## 7. Azure Data Factory Validation

An Azure Data Factory pipeline named:

```text
pl_olist_bronze_validation
```

validates the required Bronze-layer files.

The pipeline:

1. Retrieves the list of files in the Bronze folder.
2. Checks for the required datasets and ingestion manifest.
3. Evaluates whether the required files are present.
4. Fails with an explicit error if required files are missing.

The pipeline uses:

* `ls_adls_olist`
* `ds_olist_bronze_folder`
* `ds_olist_bronze_file`

**Important:** The Azure Data Factory pipeline currently performs Bronze-layer file validation. The complete Bronze-to-Silver-to-Gold processing workflow is orchestrated by the Python script `src/run_pipeline.py`.

A successful ADF validation run was recorded.

## 8. Infrastructure as Code

Azure infrastructure is defined using Bicep templates in the `infrastructure/` directory.

The infrastructure deployment provisions the required Azure resources and configures the project environment.

This approach supports repeatable infrastructure deployment and reduces the need for manual resource configuration.

## 9. Repository Structure

```text
azure-lakehouse-platform/
|
|-- data/
|   |-- bronze/
|   |-- silver/
|   |-- gold/
|
|-- infrastructure/
|
|-- src/
|   |-- quality/
|   |   |-- gold_quality_checks.py
|   |
|   |-- ingest_olist.py
|   |-- transform_olist_silver.py
|   |-- build_olist_gold.py
|   |-- upload_to_adls.py
|   |-- run_pipeline.py
|
|-- tests/
|   |-- test_gold_quality_checks.py
|
|-- dbt/
|
|-- sql/
|
|-- notebooks/
|
|-- .github/
|
|-- requirements.txt
|-- README.md
```

## 10. Environment Setup

### Prerequisites

* Python 3.13
* Git
* Azure CLI
* An Azure subscription with access to the required resources

### Install Dependencies

Install the project dependencies:

```cmd
python -m pip install -r requirements.txt
```

### Azure Authentication

Sign in to Azure:

```cmd
az login
```

Check the active subscription:

```cmd
az account show
```

Ensure the signed-in account has the required permissions to access the Azure resources.

### Run Automated Tests

From the project root:

```cmd
python -m pytest -q
```

## 11. Verified Execution Results

The following results were recorded during successful project execution.

| Component              | Verified result               |
| ---------------------- | ----------------------------- |
| Bronze ingestion       | 9 datasets processed          |
| Silver transformation  | 9 datasets processed          |
| Gold modelling         | 6 analytical tables generated |
| Gold quality checks    | 49 checks passed              |
| Automated test suite   | 24 tests passed               |
| Bronze upload          | 10 files                      |
| Silver upload          | 10 files                      |
| Gold upload            | 8 files                       |
| Total ADLS Gen2 upload | 28 files                      |
| ADF Bronze validation  | Succeeded                     |

### Final Execution Status

```text
BRONZE INGESTION             SUCCESS
SILVER TRANSFORMATION        SUCCESS
GOLD ANALYTICAL MODELLING    SUCCESS
GOLD DATA QUALITY            49 CHECKS PASSED
AUTOMATED TESTS              24 PASSED
ADLS GEN2 UPLOAD             28 FILES
ADF VALIDATION               SUCCEEDED

OVERALL STATUS: SUCCESS
```

## 12. Project Objective

This project demonstrates practical cloud data engineering capabilities through the implementation of an end-to-end lakehouse platform.

It brings together data ingestion, data transformation, analytical modelling, data quality assurance, automated testing, infrastructure deployment and Azure cloud storage integration.
