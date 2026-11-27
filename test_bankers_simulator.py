"""Focused tests for the Banker's Algorithm calculations and decisions."""

import unittest

from bankers_simulator import BankerState, InputError, check_request, check_safety


def textbook_state() -> BankerState:
    return BankerState(
        process_ids=("P0", "P1", "P2", "P3", "P4"),
        resource_ids=("A", "B", "C"),
        total=(10, 5, 7),
        allocation=(
            (0, 1, 0),
            (2, 0, 0),
            (3, 0, 2),
            (2, 1, 1),
            (0, 0, 2),
        ),
        maximum=(
            (7, 5, 3),
            (3, 2, 2),
            (9, 0, 2),
            (2, 2, 2),
            (4, 3, 3),
        ),
    )


class BankerAlgorithmTests(unittest.TestCase):
    def test_textbook_state_is_safe_and_computes_expected_vectors(self) -> None:
        state = textbook_state()
        result = check_safety(state)

        self.assertEqual(state.allocated_total, (7, 2, 5))
        self.assertEqual(state.available, (3, 3, 2))
        self.assertEqual(state.need[0], (7, 4, 3))
        self.assertTrue(result.safe)
        self.assertEqual(result.safe_sequence, ("P1", "P3", "P0", "P2", "P4"))
        self.assertEqual(result.final_work, (10, 5, 7))
        self.assertEqual(result.finish, (True, True, True, True, True))

    def test_circular_wait_example_is_unsafe(self) -> None:
        state = BankerState(
            process_ids=("P0", "P1"),
            resource_ids=("A", "B"),
            total=(1, 1),
            allocation=((1, 0), (0, 1)),
            maximum=((1, 1), (1, 1)),
        )
        result = check_safety(state)

        self.assertFalse(result.safe)
        self.assertEqual(result.safe_sequence, ())
        self.assertEqual(result.finish, (False, False))
        self.assertEqual(result.final_work, (0, 0))

    def test_safe_request_is_granted_after_tentative_safety_check(self) -> None:
        result = check_request(textbook_state(), 1, (1, 0, 2))

        self.assertEqual(result.status, "GRANTED")
        self.assertIsNotNone(result.tentative_state)
        self.assertEqual(result.tentative_state.available, (2, 3, 0))
        self.assertEqual(result.tentative_state.allocation[1], (3, 0, 2))
        self.assertEqual(result.tentative_state.need[1], (0, 2, 0))
        self.assertTrue(result.safety_result.safe)

    def test_request_waits_when_available_is_too_small(self) -> None:
        result = check_request(textbook_state(), 0, (4, 0, 0))

        self.assertEqual(result.status, "WAIT")
        self.assertIsNone(result.tentative_state)
        self.assertIn("Available", result.reason)

    def test_request_beyond_remaining_need_is_rejected(self) -> None:
        result = check_request(textbook_state(), 2, (0, 0, 1))

        self.assertEqual(result.status, "REJECTED")
        self.assertIsNone(result.tentative_state)
        self.assertIn("remaining Need", result.reason)

    def test_invalid_allocation_above_total_is_rejected(self) -> None:
        with self.assertRaises(InputError):
            BankerState(
                process_ids=("P0",),
                resource_ids=("A",),
                total=(1,),
                allocation=((2,),),
                maximum=((2,),),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
