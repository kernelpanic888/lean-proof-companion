import unittest
from lean_proof_companion.dialogue import repetitive

class DialogueSafetyTests(unittest.TestCase):
    def test_screenshot_style_loop_is_detected(self):
        self.assertTrue(repetitive('![](https://bad/'+'category_theory_'*12))
    def test_short_and_useful_text_is_not_a_loop(self):
        self.assertFalse(repetitive('2 + 2 = 4. Lean проверяет формальное утверждение.'))
    def test_repeated_prose_loop_is_detected(self):
        self.assertTrue(repetitive('Не следует это повторять. '*8))
