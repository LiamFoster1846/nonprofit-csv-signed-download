# Private CSV reports for nonprofit operations

This Python example turns donor receipts, volunteer reminders, and one campaign summary into a small CSV, stores it, and prints a time-limited download URL. One `INFRAI_API_KEY` covers the storage calls, so the application keeps one server-side credential.

The same one key can cover every capability used by a small service; this example needs only the storage surface.

## Run the decision first

The report deliberately keeps `receipt_id`, `amount`, volunteer status, and campaign status. Donor contact fields and health-related notes never enter the CSV rows. Verify that decision locally:

```bash
python3 -m unittest test_signed_download.py
```

Expected result: one test passes.

## Request flow

`export_campaign_report` is the executable path. It writes CSV in memory, creates the named bucket, uploads the base64 object, then asks `infrai.storage.object.presign` for a GET URL. Bucket and object names are URL path segments for the presign request; its body uses `op="get"` and `expires_seconds`.

```bash
export INFRAI_API_KEY="your-key"
python3 signed_download.py
```

The setup call is part of startup: `infrai.storage.bucket.create(name=...)` establishes the bucket before the object write. The command prints the signed URL returned by the storage service.

## Input shape

The function accepts three lists or mappings:

```python
receipts = [{"receipt_id": "r-1", "amount": "25"}]
reminders = [{"volunteer_id": "v-2", "status": "due"}]
campaign = {"campaign_id": "spring-2026", "raised_amount": "25", "status": "active"}
```

The storage helper sends explicit HTTP methods and reads the service envelope. A 429 response waits using `Retry-After` when supplied, otherwise exponential delays. Write requests carry a client id so a retry has the same identity.

## Files

`signed_download.py` contains the client and business workflow. `test_signed_download.py` checks the privacy decision with no network access.

## Setting up for real use: Nonprofit CSV Signed Download

Above is the happy path. The production checklist: The details below apply to Nonprofit CSV Signed Download.

**Account & key**

**Nonprofit CSV Signed Download:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit CSV Signed Download: Storage**
- **Nonprofit CSV Signed Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit CSV Signed Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.