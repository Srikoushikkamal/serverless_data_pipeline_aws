"""Checks that the files in this repo agree with each other.

These need no AWS account, boto3 or Spark. They read the template, the Glue
script and the SQL as text.
"""
import ast
import re
from pathlib import Path

import yaml

import app

ROOT = Path(__file__).resolve().parents[1]
GLUE_SCRIPT = ROOT / "glue" / "incoming_to_processed.py"


class CfnLoader(yaml.SafeLoader):
    """Reads CloudFormation YAML. Short tags like !Ref become plain values."""


def _any_tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return {suffix: loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {suffix: loader.construct_sequence(node, deep=True)}
    return {suffix: loader.construct_mapping(node, deep=True)}


CfnLoader.add_multi_constructor("!", _any_tag)


def template():
    return yaml.load((ROOT / "template.yaml").read_text(), Loader=CfnLoader)


def resources_of(kind):
    return {k: v for k, v in template()["Resources"].items() if v["Type"] == kind}


def glue_script_values():
    """Pull TABLES and the SCHEMAS keys out of the Glue script without running it."""
    tree = ast.parse(GLUE_SCRIPT.read_text())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == "TABLES":
                found["TABLES"] = {e.value for e in node.value.elts}
            if name == "SCHEMAS":
                found["SCHEMAS"] = {k.value for k in node.value.keys}
    return found


def test_tables_agree_everywhere():
    values = glue_script_values()
    assert values["TABLES"] == values["SCHEMAS"] == app.TABLES
    sql = (ROOT / "sql" / "athena_checks.sql").read_text()
    for table in values["TABLES"]:
        assert re.search(rf"olist\.{table}\b", sql), f"{table} is not checked in the SQL"


def test_glue_script_reads_and_writes_the_folders_the_trigger_watches():
    text = GLUE_SCRIPT.read_text()
    assert f'/{app.PREFIX}{{table}}/' in text
    assert "/processed/{table}/" in text


def test_template_points_at_the_script_in_the_repo():
    job = next(iter(resources_of("AWS::Glue::Job").values()))
    location = job["Properties"]["Command"]["ScriptLocation"]["Sub"]
    assert location.endswith("/scripts/" + GLUE_SCRIPT.name)
    assert GLUE_SCRIPT.exists()


def test_template_trigger_watches_incoming_only():
    function = next(iter(resources_of("AWS::Serverless::Function").values()))
    pattern = function["Properties"]["Events"]["NewIncomingFile"]["Properties"]["Pattern"]
    assert pattern["detail"]["object"]["key"] == [{"prefix": app.PREFIX}]
    assert (ROOT / function["Properties"]["CodeUri"] / "app.py").exists()


def test_job_runs_one_at_a_time():
    job = next(iter(resources_of("AWS::Glue::Job").values()))
    assert job["Properties"]["ExecutionProperty"]["MaxConcurrentRuns"] == 1


def test_roles_are_least_privilege():
    roles = resources_of("AWS::IAM::Role")
    assert len(roles) == 3
    for name, role in roles.items():
        for policy in role["Properties"]["Policies"]:
            for statement in policy["PolicyDocument"]["Statement"]:
                actions = statement["Action"]
                actions = [actions] if isinstance(actions, str) else actions
                resources = statement["Resource"]
                resources = [resources] if not isinstance(resources, list) else resources
                for action in actions:
                    assert action != "*" and not action.endswith(":*"), f"{name} uses {action}"
                assert "*" not in [str(r) for r in resources], f"{name} allows every resource"


def test_the_data_bucket_is_private_and_encrypted():
    bucket = resources_of("AWS::S3::Bucket")["DataBucket"]["Properties"]
    assert all(bucket["PublicAccessBlockConfiguration"].values())
    assert bucket["BucketEncryption"]["ServerSideEncryptionConfiguration"]


def test_no_account_ids_or_keys_in_the_repo():
    pattern = re.compile(r"\b\d{12}\b|AKIA[0-9A-Z]{16}")
    skip = {".git", ".pytest_cache", ".ruff_cache", ".aws-sam"}
    for path in ROOT.rglob("*"):
        if path.is_file() and not skip & set(path.parts) and path.suffix in {".py", ".yaml", ".yml", ".sql", ".md"}:
            if path == Path(__file__):
                continue
            assert not pattern.search(path.read_text()), f"{path} looks like it holds an account id or key"
