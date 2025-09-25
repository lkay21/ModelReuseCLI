from unittest.mock import patch
from tests.base import BaseCLITestCase
from model import Model, Code, Dataset

class MetricsContractTests(BaseCLITestCase):
    def setUp(self):
        self.model = Model(url="https://huggingface.co/org/model", id="org/model")
        self.model.linkCode(Code("https://github.com/org/repo"))
        self.model.linkDataset(Dataset("https://huggingface.co/datasets/org/data"))

    def test_calc_metrics_parallel_produces_scores_and_latencies(self):
        # Patch heavy bits inline so test stays offline & deterministic
        def _fake_calc_code_quality(self):
            self.metrics["code_quality"] = 0.60
            self.latencies["code_quality_latency"] = 0.0

        with patch("classes.model.size_score", return_value=0.42), \
             patch("classes.model.ramp_up_time", return_value=0.80), \
             patch.object(Model, "calcCodeQuality", _fake_calc_code_quality):

            self.model.calcMetricsParallel()

        for _, v in self.model.metrics.items():
            self.assertScore01(v)

        for _, v in self.model.latencies.items():
            self.assertNonNegative(v)
