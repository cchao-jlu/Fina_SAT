import unittest

from src.solving.budget import apply_rollout_budget


class RolloutBudgetTest(unittest.TestCase):
    def test_cpu_budget_sets_cpu_limit_only(self):
        params = apply_rollout_budget({"K": 0.1}, budget_type="cpu_time", cpu_lim=2, conflicts=500)

        self.assertEqual(params["cpu-lim"], 2)
        self.assertNotIn("conf-lim", params)

    def test_conflict_budget_keeps_cpu_guard_and_sets_conflict_limit(self):
        params = apply_rollout_budget({"K": 0.1}, budget_type="conflicts", cpu_lim=2, conflicts=500)

        self.assertEqual(params["cpu-lim"], 2)
        self.assertEqual(params["conf-lim"], 500)


if __name__ == "__main__":
    unittest.main()
