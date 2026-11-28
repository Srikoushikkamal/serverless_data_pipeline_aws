"""Start the Glue job when a new CSV file lands under incoming/.

EventBridge sends an "Object Created" event for each new object in the data
bucket. Files are expected at incoming/<table>/<anything>.csv. Anything else is
logged and ignored, so a stray upload never starts a job.

The Glue job reads every table folder in one run, so the event only needs to
start it. If a run is already going, Glue refuses a second one. The error is
raised again so Lambda retries the event later instead of dropping it.
"""
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

PREFIX = "incoming/"
TABLES = {"customers", "orders", "order_items", "payments", "products", "reviews", "sellers"}


def table_from_key(key):
    """Return the table name for a valid incoming file key, or None."""
    if not key.startswith(PREFIX) or not key.lower().endswith(".csv"):
        return None
    parts = key[len(PREFIX):].split("/")
    if len(parts) < 2:
        return None
    return parts[0] if parts[0] in TABLES else None


def log(message, **fields):
    logger.info(json.dumps({"message": message, **fields}))


def handler(event, context, glue=None):
    detail = event.get("detail", {})
    key = detail.get("object", {}).get("key", "")
    table = table_from_key(key)

    if table is None:
        log("ignored", key=key)
        return {"started": False, "key": key}

    if glue is None:
        import boto3  # imported here so the unit tests do not need boto3

        glue = boto3.client("glue")

    job_name = os.environ["GLUE_JOB_NAME"]
    try:
        run = glue.start_job_run(JobName=job_name)
    except Exception as err:
        code = getattr(err, "response", {}).get("Error", {}).get("Code", type(err).__name__)
        log("could not start job", key=key, job=job_name, error=code)
        raise

    log("job started", key=key, table=table, job=job_name, job_run_id=run["JobRunId"])
    return {"started": True, "table": table, "job_run_id": run["JobRunId"]}
