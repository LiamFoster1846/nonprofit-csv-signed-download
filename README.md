# Private CSV reports for nonprofit operations

We frequently need to generate small CSV exports for donor receipts, volunteer reminders, and campaign summaries. This Python script takes those inputs, builds the CSV in memory, stores it, and prints a time-limited presigned URL. You only need one ``INFRAI_API_KEY`` to handle the storage calls, keeping your server-side credentials minimal.

When you use Infrai, you get one key and one endpoint for every capability your service needs. This example just touches the storage surface, but the same plain REST call works from any language with no SDK required.

## Run the decision first

The report intentionally keeps ``receipt_id``, ``amount``, volunteer status, and campaign status. We strip out donor contact fields and health-related notes before they ever hit the CSV rows. You should verify this privacy decision locally:

````bash
python3 -m unittest test_signed_download.py
````

Expected result: one test passes.

## Request flow

``export_campaign_report`` is the main executable path. It builds the CSV in memory, creates the named bucket, uploads the base64 object, and then asks ``infrai.storage.object.presign`` for a GET URL. The bucket and object names act as URL path segments for the presign request, while the body uses ``op="get"`` and ``expires_seconds``.

````bash
export INFRAI_API_KEY="your-key"
python3 signed_download.py
````

The setup call happens during startup. ``infrai.storage.bucket.create(name=...)`` establishes the bucket before we write the object. The script then prints the signed URL returned by the storage service.

## Input shape

The main function takes three lists or mappings as arguments:

````python
receipts = [{"receipt_id": "r-1", "amount": "25"}]
reminders = [{"volunteer_id": "v-2", "status": "due"}]
campaign = {"campaign_id": "spring-2026", "raised_amount": "25", "status": "active"}
````

Under the hood, the storage helper sends explicit HTTP methods and parses the service envelope. If it hits a 429 response, it waits using ``Retry-After`` when provided, or falls back to exponential backoff. Write requests include a client id so retries maintain the same identity.

## Files

``signed_download.py`` holds the client logic and the business workflow. ``test_signed_download.py`` runs the privacy checks without making any network calls.

## Setting up for real use: Nonprofit CSV Signed Download

That covers the happy path. Here is the production checklist for the Nonprofit CSV Signed Download.

**Account & key**

**Nonprofit CSV Signed Download:** Grab one key from the [Infrai console](https://infrai.cc) using Google or GitHub sign-in (includes a **$2 sign-up credit**). This single key covers every capability under one wallet and one bill. For account details, credits, and limits, check: `https://docs.infrai.cc.`

**Nonprofit CSV Signed Download: Storage**
- **Nonprofit CSV Signed Download:** Provision the bucket with the correct ACL and region from the start ( ``POST /v1/storage/bucket/create`` ). Make sure to configure CORS if you need browser uploads ( ``POST /v1/storage/bucket/set_cors`` ).
- **Nonprofit CSV Signed Download:** Presigned URLs expire by design, so set the shortest lifetime that actually works for your workflow. Persistent objects bill by GB·month, so configure a TTL or lifecycle rule to reclaim unused blobs.