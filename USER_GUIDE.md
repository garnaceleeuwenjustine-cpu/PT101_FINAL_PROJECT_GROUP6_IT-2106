# User Guide

## 1. Requirements

- Python 3.15
- No third-party packages
- A terminal, PowerShell, or command prompt

## 2. Start the simulator

Open a terminal in the project folder and run:

```text
py -3.15 bankers_gui.py
```

Or select the **Python 3.15** interpreter in VS Code and run:

```text
python bankers_gui.py
```

The neon nightclub-themed desktop window opens with the course sample loaded and the Fleischer’s Finest Five logo in its header. Numeric fields accept typed whole numbers, and each field also has `−` and `+` buttons. Press **Enter** or click any app button to apply typed values. Results are shown as read-only tables. Choose:

- **Safety Check** — the required Topic 5 computation.
- **Resource Request** — an optional extension that tests a tentative allocation.
- **Load Sample** — restores the five-process classroom example.
- **Reset** — sets current totals, allocations, Max values, and request values to zero.

Type into a numeric field or use its `−` and `+` buttons to change process count, resource count, Total, Allocation, Max, and Request values. Process count is limited to 1–8, resource count to 1–5, and unit values to 0–99. Fields accept digits only; values outside their current allowed range are clamped when applied. Process labels are generated as `P0`, `P1`, and so on; resource labels are generated as A through E. Increasing or decreasing the process or resource count preserves matching rows and columns where possible.

The controls enforce these limits before a value changes:

- Total cannot be reduced below the units currently allocated for that resource.
- Allocation cannot exceed the process’s Max or the unallocated system Total.
- Max cannot be reduced below the current Allocation.
- Request values stay between 0 and 99. Requests above Need or Available can still be selected so the program can demonstrate `REJECTED` and `WAIT` results.

## 3. Set the system state

The sample is loaded by default. To create another state:

1. Type process/resource counts or use their `−`/`+` controls to set matrix size.
2. Type each resource Total or use its `−`/`+` controls.
3. Type each Allocation and Max value or use its `−`/`+` controls.
4. Choose **Safety Check** and run the algorithm.

The matrix uses automatic process labels (`P0`, `P1`, ...) and resource labels (`A`, `B`, ...). Disabled buttons mark values at their allowed limits.

### Classroom example

The following values use resource order `A B C`:

```text
Processes: 5
Resources: A B C
Total: 10 5 7
Allocation P0: 0 1 0
Allocation P1: 2 0 0
Allocation P2: 3 0 2
Allocation P3: 2 1 1
Allocation P4: 0 0 2
Max P0: 7 5 3
Max P1: 3 2 2
Max P2: 9 0 2
Max P3: 2 2 2
Max P4: 4 3 3
```

The default sample matches these values. Use **Load Sample** to restore them at any time.

## 4. Read the output

After a check, select the results tab that you need:

- **Need Matrix** — each process’s Allocation, Max, and calculated Need.
- **Safety Trace** — each process check, its Need and Work vectors, eligibility result, released Allocation, and updated Finish flags.
- **Request Checks** — the request-to-Need and request-to-Available comparisons, tentative safety result, and final decision.

In **Safety Trace**, the first row shows the starting Work and Finish state. In the Finish column, `✓` means True (finished) and `·` means False (not finished).

The summary cards above the tables show:

- **Total** — all instances in the system.
- **Allocation totals** — the sum of each Allocation column.
- **Available** — `Total − Allocation totals`.
- **Need** — `Max − Allocation` for each process and resource.

The safety trace starts with `Work = Available` and all Finish flags set to `False`. Each line compares a process’s remaining Need with the current Work vector component by component. `PASS` means the process can finish now; the simulator then adds that process’s Allocation back to Work and marks its Finish flag `True`. It restarts its scan from `P0` after each completion.

If every Finish flag becomes `True`, the state is **SAFE** and the listed order is one safe sequence. If a complete scan finds no eligible unfinished process, the state is **UNSAFE**, and the remaining processes are shown. The sequence depends on the order in which the simulator scans processes; more than one safe sequence may exist.

## 5. Check a resource request

Choose **Resource Request**, then use the process arrows and Request `−`/`+` controls to select:

- Requesting process, such as `P1`.
- Request vector in the selected resource order.

The program checks:

1. `Request <= Need`. If false, the request is `REJECTED` because it exceeds the process’s declared remaining claim.
2. `Request <= Available`. If false, the result is `WAIT`; the state is unchanged.
3. Otherwise, it temporarily applies the request and runs the Safety Algorithm. A safe tentative state is `GRANTED`. An unsafe tentative state is `WAIT` and is not committed.

This menu option is an extension. The required deliverable is the Safety Algorithm.

## 6. Run the automated checks

From this folder:

```text
python -m unittest -v test_bankers_simulator.py
```

See `TEST_EVIDENCE.md` for the test scenarios and their expected and actual results.

## 7. Use the terminal fallback

The separate terminal interface accepts typed input if a graphical window cannot be opened:

```text
python bankers_simulator.py
```
