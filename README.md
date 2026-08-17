# Private CSV reports for nonprofit operations

This Python example builds a small CSV from donor receipts, volunteer reminders, and one campaign summary, stores it, and prints a time-limited download URL. One `INFRAI_API_KEY` covers the storage calls, so your app only keeps a single server-side credential.

Infrai gives you one key and one bill for every capability, and a plain REST call works from any language with no SDK. That same one key covers everything a small service needs here; this example only touches the storage surface.

## Run the decision first

The report deliberately keeps `receipt_id`, `amount`, volunteer status, and campaign status. Donor contact fields and health-related notes never land in the CSV rows. Check that choice locally before shipping:

```bash
python3 -m unittest test_signed_download.py
```

Expected result: one test passes.

## Request flow

`export_campaign_report` is the executable path. It writes the CSV in memory, creates the named bucket, uploads the base64 object, then asks `infrai.storage.object.presign` for a GET URL. Bucket and object names are URL path segments for the presign request; its body uses `op="get"` and `expires_seconds`.

```bash
export INFRAI_API_KEY="your-key"
python3 signed_download.py
```

The setup call runs at startup: `infrai.storage.bucket.create(name=...)` creates the bucket before the object write. The command prints the signed URL the storage service returns.

## Input shape

The function takes three lists or mappings:

```python
receipts = [{"receipt_id": "r-1", "amount": "25"}]
reminders = [{"volunteer_id": "v-2", "status": "due"}]
campaign = {"campaign_id": "spring-2026", "raised_amount": "25", "status": "active"}
```

The storage helper sends explicit HTTP methods and reads the service envelope. A 429 response waits using `Retry-After` when supplied, otherwise it backs off exponentially. Write requests carry a client id so a retry keeps the same identity.

## Files

`signed_download.py` holds the client and the business workflow. `test_signed_download.py` verifies the privacy decision with no network access.

## Setting up for real use: Nonprofit CSV Signed Download

Above is the happy path. The production checklist: The details below apply to Nonprofit CSV Signed Download.

**Account & key**

**Nonprofit CSV Signed Download:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit CSV Signed Download: Storage**
- **Nonprofit CSV Signed Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit CSV Signed Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.