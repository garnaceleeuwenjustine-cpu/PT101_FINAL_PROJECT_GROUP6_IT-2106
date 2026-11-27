# Demo Script — 5 to 8 Minutes

Use the desktop interface live; it opens with the standard safe-state example already selected. Keep a copy of the source folder available in case the classroom computer has no Python setup.

## 0:00–0:45 — Introduce the problem

“We are Fleischer’s Finest Five, also known as The Boop-Oop-A-Doos. Our assigned topic is deadlock avoidance with Banker’s Algorithm. The safety check asks whether there is some order in which every process can finish with the resources available now and those released by completed processes.”

## 0:45–1:30 — Explain the input

Show the process/resource count fields, Total, Allocation, and Max controls in the left input panel. Type a value or use the `−`/`+` steppers, then press Enter or click an app button to apply it. Explain the built-in limits: counts stay within the displayed ranges, Allocation cannot exceed Max or Total, and Max cannot drop below Allocation.

## 1:30–2:30 — Explain the derived values

Point to the summary cards and **Need Matrix** tab for the example:

- Allocation totals: `(7, 2, 5)`
- Available: `(10, 5, 7) − (7, 2, 5) = (3, 3, 2)`
- For P0, Need: `(7, 5, 3) − (0, 1, 0) = (7, 4, 3)`

## 2:30–4:30 — Trace the safety check

Explain that a process can finish only if every Need component is less than or equal to the matching Work component. The program tests processes in label order and restarts its scan after a process completes.

Click **Safety Check** and run the sample. Open the **Safety Trace** table. The first eligible process is P1. Its Allocation `(2, 0, 0)` is returned, changing Work from `(3, 3, 2)` to `(5, 3, 2)`. Continue through the table until all Finish flags are True. The sequence produced by this implementation is `P1 -> P3 -> P0 -> P2 -> P4`.

## 4:30–5:30 — Show an unsafe state

If time permits, use two resources with Total `(1,1)`, Allocation `P0=(1,0), P1=(0,1)`, and Max `(1,1)` for both. Available is `(0,0)` and both processes still need one resource, so no process can finish in the safety simulation. Explain that UNSAFE means safety cannot be guaranteed; it does not alone prove a deadlock has already occurred.

## 5:30–6:30 — Show the request extension

Choose **Resource Request**. The sample request `(1,0,2)` for P1 is preloaded. Explain the checks against Need and Available, the tentative allocation, and why the request is granted only after the tentative state passes the safety check.

## 6:30–7:00 — Close

Summarize the key rule: if `Need <= Work`, the process can finish in the simulated order and releases its Allocation back into Work. The group should invite questions and be ready to explain any line of the trace or code.
