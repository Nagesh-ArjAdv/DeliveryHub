from fastapi import HTTPException, status
from typing import Dict, Optional

from models import Location 

def validate_location_data(location_data: Dict, partial: bool = False) -> Location:
    """
    Validate payload for creating or updating a Location.
    Ensures cloud, product, region, and auth fields are valid.
    """ 
    cloud = (location_data.get("cloud") or "").lower()
    product = (location_data.get("product") or "").lower()
    auth = location_data.get("auth") or {}
    bucket_info = location_data.get("bucket_info") or {}

    valid_products = {
        "aws": ["s3", "snowflake", "databricks", "redshift", "sftp"],
        "gcp": ["gcs", "bigquery", "snowflake", "databricks"],
        "azure": ["blobstorage", "snowflake", "databricks"],
    }

    # --- Cloud Validation ---
    if not partial or "cloud" in location_data:
        if not cloud:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"cloud": "Cloud is required."})
        if cloud not in valid_products:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"cloud": f"Invalid cloud: {cloud}."})

    # --- Product Validation ---
    if not partial or "product" in location_data:
        if not product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"product": "Product is required."})
        if product not in valid_products[cloud]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "product": f"Invalid product '{product}' for cloud '{cloud}'. "
                               f"Valid options: {', '.join(valid_products[cloud])}."
                },
            )

    # --- Bucket Info Validation ---
    if not partial or "bucket_info" in location_data:
        region = bucket_info.get("region")
        bucket_name = bucket_info.get("bucket_name")
        path = bucket_info.get("path")
        is_external = bucket_info.get("is_external")

        if not region:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"region": "Region is required."})
        if not bucket_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"bucket_name": "Bucket name is required."})
        if not path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"path": "Path is required."})
        if is_external is None:   # ✅ allows False
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"is_external": "is_external is required."})

    # --- Auth Validation ---
    if not partial or "auth" in location_data:
        if not isinstance(auth, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"auth": "Auth must be a JSON object."})

        auth_type = auth.get("type")
        required_keys = []

        # ---- AWS / S3 ----
        if cloud == "aws" and product == "s3":
            if not auth_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"auth": "Auth 'type' is required for AWS S3."})
            if auth_type not in ["ASSUME_ROLE", "CONSUMER_ROLE", "ACCESS_KEY"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"auth": f"Invalid auth type '{auth_type}' for AWS S3. Allowed: ASSUME_ROLE, CONSUMER_ROLE, ACCESS_KEY."})
            
            if auth_type == "ASSUME_ROLE":
                required_keys = ["arn"]
            elif auth_type == "CONSUMER_ROLE":
                required_keys = ["arn", "consumerArn"]
            elif auth_type == "ACCESS_KEY":
                required_keys = ["accessKey", "secretAccessKey"]

          # --- Final key check ---
        missing = [k for k in required_keys if k not in auth]
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"auth": f"Missing required keys for {cloud} {product}: {', '.join(missing)}"})

    return Location(**location_data)        

        # # ---- GCP / GCS ----
        # elif cloud == "gcp" and product == "gcs":
        #     if not auth_type:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"auth": "Auth 'type' is required for GCP GCS."})
        #     if auth_type not in ["EXTERNAL_ACCESS", "IMPERSONATION"]:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"auth": f"Invalid auth type '{auth_type}' for GCP GCS. Allowed: EXTERNAL_ACCESS, IMPERSONATION."})

        #     if auth_type == "IMPERSONATION":
        #         required_keys = ["serviceAccountToImpersonate"]

        # # ---- Azure Blob ----
        # elif cloud == "azure" and product == "blobstorage":
        #     access_identifiers = auth.get("accessIdentifiers")
        #     if not access_identifiers or not isinstance(access_identifiers, dict):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"auth": "accessIdentifiers (dict) is required for Azure Blob Storage."})

        #     apps = access_identifiers.get("consumerManagedApplications")
        #     if not apps or not isinstance(apps, list):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"auth": "consumerManagedApplications must be a list with at least one item."})

        #     for app in apps:
        #         if "applicationId" not in app:
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={"auth": "Each application must include 'applicationId'."})

        # # ---- Snowflake ----
        # elif product == "snowflake" and cloud in ["aws", "gcp", "azure"]:
        #     access_identifiers = auth.get("accessIdentifiers")
        #     if not access_identifiers or not isinstance(access_identifiers, list):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"accessIdentifiers": "List of accessIdentifiers is required for Snowflake."})
        #     for idx, entry in enumerate(access_identifiers):
        #         if not entry.get("organizationName"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accessIdentifiers[{idx}].organizationName": "organizationName is required."})
        #         if not entry.get("accountName"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accessIdentifiers[{idx}].accountName": "accountName is required."})

        # # ---- Databricks ----
        # elif product == "databricks" and cloud in ["aws", "gcp", "azure"]:
        #     access_identifiers = auth.get("accessIdentifiers")
        #     if not access_identifiers or not isinstance(access_identifiers, list):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"accessIdentifiers": "List of accessIdentifiers is required for Databricks."})
        #     for idx, entry in enumerate(access_identifiers):
        #         if not entry.get("metastoreId"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accessIdentifiers[{idx}].metastoreId": "metastoreId is required."})

        # # ---- Redshift ----
        # elif cloud == "aws" and product == "redshift":
        #     accounts = auth.get("accounts")
        #     if not accounts or not isinstance(accounts, list):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"accounts": "accounts must be a non-empty list for Redshift."})
        #     for idx, acc in enumerate(accounts):
        #         if not acc.get("accountId"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accounts[{idx}].accountId": "accountId is required."})

        # # ---- SFTP ----
        # elif cloud == "aws" and product == "sftp":
        #     access_identifiers = auth.get("accessIdentifiers")
        #     if not access_identifiers or not isinstance(access_identifiers, list):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                             detail={"accessIdentifiers": "List of accessIdentifiers is required for SFTP."})
        #     for idx, entry in enumerate(access_identifiers):
        #         if not entry.get("label"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accessIdentifiers[{idx}].label": "label is required."})
        #         if not entry.get("publicKey"):
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        #                                 detail={f"accessIdentifiers[{idx}].publicKey": "publicKey is required."})

      



