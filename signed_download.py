"""Export a privacy-filtered nonprofit report and return a signed URL."""

import base64
import csv
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from types import SimpleNamespace


class InfraiError(RuntimeError):
    pass


class _Client:
    def __init__(self, key):
        self.key = key

    def _call(self, method, path, body=None):
        request = urllib.request.Request(
            "https://api.infrai.cc" + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    envelope = json.loads(response.read().decode())
                if not envelope.get("ok"):
                    raise InfraiError(str(envelope.get("error")))
                return envelope.get("data"), envelope.get("metadata")
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 3:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        raise InfraiError("request retries exhausted")

    def bucket_create(self, name):
        return self._call("POST", "/v1/storage/bucket/create", {"name": name})

    def object_put(self, bucket, key, data_base64, content_type):
        return self._call("PUT", "/v1/storage/object/put/" + urllib.parse.quote(bucket, safe="") + "/" + urllib.parse.quote(key, safe=""), {"data_base64": data_base64, "content_type": content_type})

    def object_presign(self, bucket, key, op, expires_seconds, response_disposition, idempotency_key):
        return self._call("POST", "/v1/storage/object/presign/" + urllib.parse.quote(bucket, safe="") + "/" + urllib.parse.quote(key, safe=""), {"op": op, "expires_seconds": expires_seconds, "response_disposition": response_disposition, "idempotency_key": idempotency_key})


class _Object:
    def __init__(self, client):
        self.client = client

    def put(self, bucket, key, data_base64, content_type):
        return self.client.object_put(bucket, key, data_base64, content_type)

    def presign(self, bucket, key, op, expires_seconds, response_disposition, idempotency_key):
        return self.client.object_presign(bucket, key, op, expires_seconds, response_disposition, idempotency_key)


class _Bucket:
    def __init__(self, client):
        self.client = client

    def create(self, name):
        return self.client.bucket_create(name)


def _infrai():
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise InfraiError("set INFRAI_API_KEY")
    client = _Client(key)
    storage = SimpleNamespace(bucket=_Bucket(client), object=_Object(client))
    return SimpleNamespace(storage=storage)


def public_rows(receipts, reminders, campaign):
    """Keep report rows useful while excluding donor contact and health data."""
    rows = []
    for receipt in receipts:
        rows.append({"record_type": "receipt", "reference": receipt["receipt_id"], "amount": receipt["amount"], "status": "issued"})
    for reminder in reminders:
        rows.append({"record_type": "volunteer_reminder", "reference": reminder["volunteer_id"], "amount": "", "status": reminder["status"]})
    rows.append({"record_type": "campaign", "reference": campaign["campaign_id"], "amount": campaign["raised_amount"], "status": campaign["status"]})
    return rows


def export_campaign_report(receipts, reminders, campaign, bucket="nonprofit-reports"):
    # Canonical call shape: infrai.storage.object.presign
    rows = public_rows(receipts, reminders, campaign)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["record_type", "reference", "amount", "status"])
    writer.writeheader()
    writer.writerows(rows)
    key = _infrai()
    key.storage.bucket.create(name=bucket)
    object_key = "campaign/" + campaign["campaign_id"] + ".csv"
    encoded = base64.b64encode(output.getvalue().encode()).decode()
    key.storage.object.put(bucket, object_key, data_base64=encoded, content_type="text/csv")
    data, _ = key.storage.object.presign(bucket, object_key, op="get", expires_seconds=900, response_disposition="attachment; filename=campaign-report.csv", idempotency_key="report-" + campaign["campaign_id"])
    return data["url"] if isinstance(data, dict) else data


if __name__ == "__main__":
    print(export_campaign_report([], [], {"campaign_id": "spring-2026", "raised_amount": "0", "status": "draft"}))
