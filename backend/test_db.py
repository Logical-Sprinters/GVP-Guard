"""Dependency-free unit tests for the SQLite layer: python3 -m unittest backend.test_db -v"""
import tempfile
import unittest
from pathlib import Path

from backend import db


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.DATA_DIR = Path(self.tmp.name)
        db.DB_PATH = db.DATA_DIR / 'test.db'
        db.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def _incident(self, ident='INC-1', **extra):
        payload = {
            'id': ident, 'time': '2026-11-05 10:00', 'location': 'GVP-01',
            'decision': 'Pending', 'statusCode': 'REVIEW_REQUIRED',
            'plate': 'Manual review pending', 'demo': False
        }
        payload.update(extra)
        return payload

    def test_create_read_patch_and_audit(self):
        db.upsert_incident(self._incident())
        self.assertEqual(len(db.list_incidents()), 1)
        self.assertEqual(db.get_incident('INC-1')['location'], 'GVP-01')
        db.patch_incident('INC-1', {'decision': 'Cleanup requested', 'statusCode': 'CLEANUP_REQUESTED'})
        self.assertEqual(db.get_incident('INC-1')['statusCode'], 'CLEANUP_REQUESTED')
        actions = [row['action'] for row in db.get_audit('INC-1')]
        self.assertEqual(actions, ['CREATE', 'UPDATE'])

    def test_decision_writes_decision_and_audit_rows(self):
        db.upsert_incident(self._incident())
        db.add_decision('INC-1', 'Approved for follow-up', 'Demo officer', 'looks valid', None)
        self.assertEqual(len(db.get_decisions('INC-1')), 1)
        self.assertIn('DECISION', [row['action'] for row in db.get_audit('INC-1')])

    def test_filters_and_summary(self):
        db.upsert_incident(self._incident('A', location='GVP-01', decision='Approved for follow-up', statusCode='APPROVED'))
        db.upsert_incident(self._incident('B', location='GVP-02', decision='Cleanup requested', statusCode='CLEANUP_REQUESTED'))
        db.upsert_incident(self._incident('C', location='GVP-02', demo=True))
        self.assertEqual(len(db.list_incidents(location='GVP-02')), 2)
        self.assertEqual(len(db.list_incidents(status='REVIEW_REQUIRED')), 1)
        summary = db.summary()
        self.assertEqual(summary['totalIncidents'], 3)
        self.assertEqual(summary['approved'], 1)
        self.assertEqual(summary['cleanupRequested'], 1)
        self.assertEqual(summary['demoRecords'], 1)

    def test_gvps_priority_is_transparent_and_capped(self):
        for i in range(30):
            db.upsert_incident(self._incident(f'INC-{i}', location='GVP-01', decision='Cleanup requested'))
        zones = {z['id']: z for z in db.gvps()}
        self.assertEqual(zones['GVP-01']['incidentCount'], 30)
        self.assertEqual(zones['GVP-01']['priorityScore'], 100)
        self.assertEqual(db.priority_score(0, 0, 0), 5)

    def test_clear_removes_incidents_but_keeps_audit(self):
        db.upsert_incident(self._incident())
        db.delete_all_incidents()
        self.assertEqual(db.list_incidents(), [])
        self.assertTrue(any(row['action'] == 'CLEAR' for row in db.get_audit('*')))

    def test_cleanup_request_create_and_get(self):
        db.upsert_incident(self._incident())
        row = db.add_cleanup_request('INC-1', assigned_to='Officer A')
        self.assertIsNotNone(row)
        self.assertEqual(row['incident_id'], 'INC-1')
        self.assertEqual(row['status'], 'requested')
        self.assertEqual(row['assigned_to'], 'Officer A')
        self.assertIsNotNone(row['requested_at'])
        self.assertIsNone(row['completed_at'])

        fetched = db.get_cleanup_request(row['id'])
        self.assertEqual(fetched['status'], 'requested')
        self.assertEqual(fetched['assigned_to'], 'Officer A')

    def test_cleanup_requests_listed_by_incident(self):
        db.upsert_incident(self._incident('INC-1'))
        db.upsert_incident(self._incident('INC-2'))
        db.add_cleanup_request('INC-1', assigned_to='Officer A')
        db.add_cleanup_request('INC-1', assigned_to='Officer B')
        db.add_cleanup_request('INC-2', assigned_to='Officer C')

        inc1 = db.get_cleanup_requests('INC-1')
        self.assertEqual(len(inc1), 2)
        inc2 = db.get_cleanup_requests('INC-2')
        self.assertEqual(len(inc2), 1)

    def test_cleanup_request_update_status(self):
        db.upsert_incident(self._incident())
        row = db.add_cleanup_request('INC-1')
        updated = db.update_cleanup_request(row['id'], {'status': 'completed'})
        self.assertEqual(updated['status'], 'completed')
        self.assertIsNotNone(updated['completed_at'])

    def test_cleanup_request_audit_trail(self):
        db.upsert_incident(self._incident())
        db.add_cleanup_request('INC-1', assigned_to='Officer A')
        actions = [r['action'] for r in db.get_audit('INC-1')]
        self.assertIn('CLEANUP_REQUESTED', actions)

    def test_delete_all_cleanup_requests(self):
        db.upsert_incident(self._incident())
        db.add_cleanup_request('INC-1')
        self.assertEqual(len(db.get_cleanup_requests()), 1)
        db.delete_all_cleanup_requests()
        self.assertEqual(len(db.get_cleanup_requests()), 0)


if __name__ == '__main__':
    unittest.main()
