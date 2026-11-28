import pytest

import app


class FakeGlue:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def start_job_run(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"JobRunId": "jr_123"}


class ConcurrentRuns(Exception):
    response = {"Error": {"Code": "ConcurrentRunsExceededException"}}


def event_for(key):
    return {"detail": {"bucket": {"name": "any-bucket"}, "object": {"key": key}}}


@pytest.fixture(autouse=True)
def job_name(monkeypatch):
    monkeypatch.setenv("GLUE_JOB_NAME", "olist-pipeline-incoming-to-processed")


@pytest.mark.parametrize("key,table", [
    ("incoming/orders/orders_2026-01-01.csv", "orders"),
    ("incoming/order_items/2026-01-01/items.csv", "order_items"),
    ("incoming/sellers/SELLERS.CSV", "sellers"),
])
def test_valid_file_starts_the_job(key, table):
    glue = FakeGlue()
    result = app.handler(event_for(key), None, glue=glue)
    assert result == {"started": True, "table": table, "job_run_id": "jr_123"}
    assert glue.calls == [{"JobName": "olist-pipeline-incoming-to-processed"}]


@pytest.mark.parametrize("key", [
    "processed/orders/part-0000.parquet",   # output folder, would loop forever
    "incoming/orders/readme.txt",           # not a csv
    "incoming/orders.csv",                  # no table folder
    "incoming/unknown_table/file.csv",      # not one of the 7 tables
    "scripts/incoming_to_processed.py",
    "",
])
def test_other_files_are_ignored(key):
    glue = FakeGlue()
    result = app.handler(event_for(key), None, glue=glue)
    assert result["started"] is False
    assert glue.calls == []


def test_missing_detail_is_ignored():
    glue = FakeGlue()
    assert app.handler({}, None, glue=glue)["started"] is False
    assert glue.calls == []


def test_error_is_raised_again_so_lambda_retries():
    glue = FakeGlue(error=ConcurrentRuns("a run is already going"))
    with pytest.raises(ConcurrentRuns):
        app.handler(event_for("incoming/orders/a.csv"), None, glue=glue)
