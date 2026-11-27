# Testing Evidence

The program was checked with Python’s built-in `unittest` runner. The command completed with **6 tests passing**.

```text
python -m unittest -v test_bankers_simulator.py
Ran 6 tests
OK
```

## Required scenarios

| Case | Input summary | Expected result | Actual result |
|---|---|---|---|
| 1 — Safe state | Total `(10, 5, 7)` and the five-process Allocation/Max matrices in `USER_GUIDE.md` | Available `(3, 3, 2)`; state SAFE; all Finish flags True | Available `(3, 3, 2)`; SAFE; all Finish flags True |
| 2 — Unsafe state | Total `(1, 1)`; Allocation `P0=(1,0), P1=(0,1)`; Max `P0=(1,1), P1=(1,1)` | Work `(0,0)`; neither process can finish; state UNSAFE | Work `(0,0)`; neither process can finish; UNSAFE; Finish `[False, False]` |
| 3 — Resource request | Baseline from Case 1; `P1` requests `(1,0,2)` | Request is within Need and Available; tentative state is safe; GRANTED | GRANTED; tentative Available `(2,3,0)`; tentative Need for P1 `(0,2,0)`; safety check passes |

The deterministic process scan for Case 1 produces this valid sequence:

```text
P1 -> P3 -> P0 -> P2 -> P4
```

The code also checks that a request beyond Available returns WAIT, a request beyond remaining Need is REJECTED, and inconsistent Allocation data is rejected. Those cases are included among the six passing tests.

## Reproduce

Run this command from the project folder:

```text
python -m unittest -v test_bankers_simulator.py
```

For submission, the group can add terminal screenshots from its own machine if the instructor expects image-based evidence. The test cases and recorded results above are the reproducible evidence produced for this project draft.
