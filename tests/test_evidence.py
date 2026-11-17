import json
import tempfile
import unittest
from pathlib import Path
from lean_proof_companion.core import TaskSpec, atomic, digest, read_result

class EvidenceTests(unittest.TestCase):
    def test_reference_is_not_part_of_identity(self):
        a=TaskSpec('x','','theorem x : True',reference='by trivial')
        b=TaskSpec('x','','theorem x : True',reference='by exact True.intro')
        self.assertEqual(a.task_id,b.task_id)
        self.assertNotEqual(a.task_id,TaskSpec('x','','theorem x : False').task_id)
    def test_result_and_file_corruption_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'proof.txt').write_text('by rfl')
            result={'files':{'proof.txt':digest(root/'proof.txt')},'accepted':True}
            atomic(root/'result.json',result);atomic(root/'seal.json',{'result_sha256':digest(root/'result.json')})
            self.assertTrue(read_result(root)['accepted'])
            (root/'proof.txt').write_text('by sorry')
            with self.assertRaises(ValueError):read_result(root)
            atomic(root/'result.json',{'accepted':True})
            with self.assertRaises(ValueError):read_result(root)
    def test_manifest_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);atomic(root/'result.json',{'files':{'../outside':'no'}})
            atomic(root/'seal.json',{'result_sha256':digest(root/'result.json')})
            with self.assertRaisesRegex(ValueError,'unsafe evidence path'):read_result(root)
