import unittest
from engine import investigate, DEMO
class EngineTests(unittest.TestCase):
 def test_demo_root_cause(self):
  result=investigate(DEMO)
  self.assertEqual(result['hypotheses'][0]['key'],'connection_pool')
  self.assertTrue(result['hypotheses'][0]['evidence'])
 def test_intervention_removes_evidence(self):
  result=investigate(DEMO,'database')
  self.assertFalse(any(e['service']=='database' for e in result['events']))
  self.assertLess(result['hypotheses'][0]['score'],investigate(DEMO)['hypotheses'][0]['score'])
 def test_unknown_abstains(self):
  self.assertEqual(investigate([{'message':'ordinary request finished','service':'api'}])['status'],'insufficient evidence')
 def test_duplicates_do_not_inflate(self):
  event={'message':'redis connection refused','service':'cache'}
  self.assertEqual(investigate([event])['hypotheses'][0]['score'],investigate([event]*30)['hypotheses'][0]['score'])
 def test_invalid_input(self):
  for value in (None,[],[{}],[{'message':3}]):
   with self.assertRaises(ValueError): investigate(value)
 def test_citations_preserve_source_ids(self):
  r=investigate(DEMO,'api'); self.assertEqual(r['events'][1]['id'],'E003')
if __name__=='__main__': unittest.main()
