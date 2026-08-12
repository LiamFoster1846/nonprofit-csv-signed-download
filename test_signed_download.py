import unittest

from signed_download import public_rows


class PublicReportPolicyTest(unittest.TestCase):
    def test_report_keeps_operational_fields_and_drops_private_fields(self):
        rows = public_rows(
            [{"receipt_id": "r-1", "amount": "25", "donor_email": "hidden@example.org", "medical_note": "hidden"}],
            [{"volunteer_id": "v-2", "status": "due", "phone": "hidden"}],
            {"campaign_id": "c-3", "raised_amount": "25", "status": "active", "donor_names": "hidden"},
        )
        self.assertEqual(rows[0], {"record_type": "receipt", "reference": "r-1", "amount": "25", "status": "issued"})
        self.assertNotIn("donor_email", rows[0])
        self.assertNotIn("medical_note", rows[0])
        self.assertEqual(rows[-1]["record_type"], "campaign")


if __name__ == "__main__":
    unittest.main()
