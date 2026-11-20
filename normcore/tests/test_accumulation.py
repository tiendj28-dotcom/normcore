"""Test BR-COST-013: tích lũy và nghĩa vụ tài chính. Đối chiếu bộ dữ liệu vàng (TC-COST-04)."""
import unittest
from decimal import Decimal as D

from normcore.costing.engine import apply_accumulation


class TestAccumulation(unittest.TestCase):
    def test_tc_cost_04_golden_dv_test_a(self):
        r = apply_accumulation(D("287745.46"), "ON_COST", D("0.05"), D("0"))
        self.assertEqual(r.accumulation, D("14387.27"))
        self.assertEqual(r.calculated_price, D("302132.73"))

    def test_tc_cost_04_golden_dv_test_b(self):
        r = apply_accumulation(D("88169.70"), "ON_COST", D("0.05"), D("0"))
        self.assertEqual(r.accumulation, D("4408.49"))
        self.assertEqual(r.calculated_price, D("92578.19"))

    def test_on_price(self):
        r = apply_accumulation(D("1000"), "ON_PRICE", D("0.05"), D("0"))
        self.assertEqual(r.accumulation, D("52.63"))  # 1000*0.05/0.95
        self.assertEqual(r.calculated_price, D("1052.63"))

    def test_no_accumulation_type(self):
        r = apply_accumulation(D("1000"), None, D("0.05"), D("0"))
        self.assertEqual(r.accumulation, D("0.00"))
        self.assertEqual(r.calculated_price, D("1000.00"))

    def test_obligation(self):
        r = apply_accumulation(D("1000"), "ON_COST", D("0.05"), D("0.1"))
        self.assertEqual(r.accumulation, D("50.00"))
        self.assertEqual(r.calculated_price, D("1166.67"))  # 1050/0.9

    def test_rounding_half_up(self):
        r = apply_accumulation(D("0.10"), "ON_COST", D("0.05"), D("0"))  # 0.005 -> 0.01
        self.assertEqual(r.accumulation, D("0.01"))

    def test_invalid(self):
        for args in [
            (D("1"), "ON_COST", D("1"), D("0")),
            (D("1"), "ON_PRICE", D("1"), D("0")),
            (D("1"), "ON_COST", D("0.05"), D("1")),
            (D("1"), "BAD", D("0.05"), D("0")),
            (D("-1"), "ON_COST", D("0.05"), D("0")),
        ]:
            with self.assertRaises(ValueError):
                apply_accumulation(*args)


if __name__ == "__main__":
    unittest.main()
