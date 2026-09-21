import tempfile
import unittest

import torch

from train_rlaf import load_compatible_checkpoint


class CheckpointInitTest(unittest.TestCase):
    def test_load_compatible_checkpoint_skips_missing_and_mismatched_weights(self):
        model = torch.nn.Sequential(
            torch.nn.Linear(2, 3),
            torch.nn.Linear(3, 1),
        )
        checkpoint = {
            "0.weight": torch.ones_like(model[0].weight),
            "0.bias": torch.ones_like(model[0].bias),
            "1.weight": torch.ones((2, 3)),
            "unknown.weight": torch.ones(1),
        }

        with tempfile.NamedTemporaryFile(suffix=".pt") as tmp:
            torch.save(checkpoint, tmp.name)
            loaded, skipped = load_compatible_checkpoint(model, tmp.name)

        self.assertIn("0.weight", loaded)
        self.assertIn("0.bias", loaded)
        self.assertIn("1.weight", skipped)
        self.assertIn("unknown.weight", skipped)
        self.assertTrue(torch.allclose(model[0].weight, torch.ones_like(model[0].weight)))

    def test_load_compatible_checkpoint_prefix_extends_wider_linear_weight(self):
        model = torch.nn.Sequential(torch.nn.Linear(4, 3))
        checkpoint_weight = torch.arange(6, dtype=torch.float32).view(3, 2)
        checkpoint = {
            "0.weight": checkpoint_weight,
            "0.bias": torch.ones_like(model[0].bias),
        }

        with tempfile.NamedTemporaryFile(suffix=".pt") as tmp:
            torch.save(checkpoint, tmp.name)
            loaded, skipped = load_compatible_checkpoint(model, tmp.name)

        self.assertIn("0.weight", loaded)
        self.assertNotIn("0.weight", skipped)
        self.assertTrue(torch.allclose(model[0].weight[:, :2], checkpoint_weight))
        self.assertTrue(torch.allclose(model[0].weight[:, 2:], torch.zeros((3, 2))))
        self.assertTrue(torch.allclose(model[0].bias, torch.ones_like(model[0].bias)))


if __name__ == "__main__":
    unittest.main()
