"""Interactive Banker’s Algorithm safety and resource-request simulator.

The program calculates every result from the values entered by the user. It
does not rely on precomputed or hard-coded output.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


Vector = Tuple[int, ...]
Matrix = Tuple[Tuple[int, ...], ...]


class InputError(ValueError):
    """Raised when user-provided resource data is invalid."""


@dataclass(frozen=True)
class BankerState:
    process_ids: Tuple[str, ...]
    resource_ids: Tuple[str, ...]
    total: Vector
    allocation: Matrix
    maximum: Matrix

    def __post_init__(self) -> None:
        process_count = len(self.process_ids)
        resource_count = len(self.resource_ids)
        if process_count == 0 or resource_count == 0:
            raise InputError("Enter at least one process and one resource type.")
        if len(set(self.process_ids)) != process_count:
            raise InputError("Process labels must be unique.")
        if len(set(self.resource_ids)) != resource_count:
            raise InputError("Resource labels must be unique.")
        if len(self.total) != resource_count:
            raise InputError("The Total vector must have one value per resource type.")
        if len(self.allocation) != process_count or len(self.maximum) != process_count:
            raise InputError("Allocation and Max must have one row per process.")

        self._validate_nonnegative(self.total, "Total")
        allocated_by_resource = [0] * resource_count
        for row_index, row in enumerate(self.allocation):
            if len(row) != resource_count:
                raise InputError("Every Allocation row must match the resource count.")
            self._validate_nonnegative(row, "Allocation")
            for resource_index, amount in enumerate(row):
                allocated_by_resource[resource_index] += amount

        for row_index, row in enumerate(self.maximum):
            if len(row) != resource_count:
                raise InputError("Every Max row must match the resource count.")
            self._validate_nonnegative(row, "Max")
            for resource_index, amount in enumerate(row):
                if self.allocation[row_index][resource_index] > amount:
                    process = self.process_ids[row_index]
                    resource = self.resource_ids[resource_index]
                    raise InputError(
                        f"{process} is allocated more {resource} than its declared Max."
                    )

        for resource_index, allocated in enumerate(allocated_by_resource):
            if allocated > self.total[resource_index]:
                resource = self.resource_ids[resource_index]
                raise InputError(
                    f"Allocated {resource} ({allocated}) exceeds Total "
                    f"({self.total[resource_index]})."
                )

    @staticmethod
    def _validate_nonnegative(values: Sequence[int], label: str) -> None:
        if any(not isinstance(value, int) or value < 0 for value in values):
            raise InputError(f"{label} values must be non-negative whole numbers.")

    @property
    def allocated_total(self) -> Vector:
        return tuple(
            sum(row[column] for row in self.allocation)
            for column in range(len(self.resource_ids))
        )

    @property
    def available(self) -> Vector:
        return tuple(
            total - allocated
            for total, allocated in zip(self.total, self.allocated_total)
        )

    @property
    def need(self) -> Matrix:
        return tuple(
            tuple(maximum - allocated for maximum, allocated in zip(max_row, alloc_row))
            for alloc_row, max_row in zip(self.allocation, self.maximum)
        )


@dataclass(frozen=True)
class SafetyEvent:
    pass_number: int
    process_id: str
    need: Vector
    work_before: Vector
    can_finish: bool
    allocation_released: Optional[Vector]
    work_after: Optional[Vector]
    finish_after: Tuple[bool, ...]


@dataclass(frozen=True)
class SafetyResult:
    safe: bool
    safe_sequence: Tuple[str, ...]
    finish: Tuple[bool, ...]
    final_work: Vector
    events: Tuple[SafetyEvent, ...]


@dataclass(frozen=True)
class RequestResult:
    status: str
    reason: str
    process_id: str
    request: Vector
    tentative_state: Optional[BankerState] = None
    safety_result: Optional[SafetyResult] = None


def vector_leq(left: Sequence[int], right: Sequence[int]) -> bool:
    """Return True when left <= right for every vector component."""
    return all(a <= b for a, b in zip(left, right))


def check_safety(state: BankerState) -> SafetyResult:
    """Run the Safety Algorithm, recording each comparison and Work update."""
    work = list(state.available)
    finish = [False] * len(state.process_ids)
    sequence: List[str] = []
    events: List[SafetyEvent] = []
    pass_number = 1

    while True:
        found_process = False
        for index, process_id in enumerate(state.process_ids):
            if finish[index]:
                continue

            need = state.need[index]
            work_before = tuple(work)
            can_finish = vector_leq(need, work_before)
            if can_finish:
                released = state.allocation[index]
                work = [available + held for available, held in zip(work, released)]
                finish[index] = True
                sequence.append(process_id)
                events.append(
                    SafetyEvent(
                        pass_number=pass_number,
                        process_id=process_id,
                        need=need,
                        work_before=work_before,
                        can_finish=True,
                        allocation_released=released,
                        work_after=tuple(work),
                        finish_after=tuple(finish),
                    )
                )
                found_process = True
                break

            events.append(
                SafetyEvent(
                    pass_number=pass_number,
                    process_id=process_id,
                    need=need,
                    work_before=work_before,
                    can_finish=False,
                    allocation_released=None,
                    work_after=None,
                    finish_after=tuple(finish),
                )
            )

        if not found_process:
            break
        pass_number += 1

    return SafetyResult(
        safe=all(finish),
        safe_sequence=tuple(sequence),
        finish=tuple(finish),
        final_work=tuple(work),
        events=tuple(events),
    )


def check_request(
    state: BankerState, process_index: int, request: Sequence[int]
) -> RequestResult:
    """Check a resource request and keep an unsafe tentative state uncommitted."""
    if process_index < 0 or process_index >= len(state.process_ids):
        raise InputError("The requesting process number is outside the process list.")
    if len(request) != len(state.resource_ids):
        raise InputError("The Request vector must have one value per resource type.")
    BankerState._validate_nonnegative(request, "Request")

    process_id = state.process_ids[process_index]
    request_vector = tuple(request)
    need = state.need[process_index]
    if not vector_leq(request_vector, need):
        return RequestResult(
            "REJECTED",
            f"Request exceeds {process_id}'s remaining Need.",
            process_id,
            request_vector,
        )
    if not vector_leq(request_vector, state.available):
        return RequestResult(
            "WAIT",
            "Request exceeds Available resources; the state is unchanged.",
            process_id,
            request_vector,
        )

    allocation = [list(row) for row in state.allocation]
    allocation[process_index] = [
        held + requested for held, requested in zip(allocation[process_index], request_vector)
    ]
    tentative_state = BankerState(
        process_ids=state.process_ids,
        resource_ids=state.resource_ids,
        total=state.total,
        allocation=tuple(tuple(row) for row in allocation),
        maximum=state.maximum,
    )
    safety_result = check_safety(tentative_state)
    if safety_result.safe:
        return RequestResult(
            "GRANTED",
            "The tentative allocation leaves the system in a safe state.",
            process_id,
            request_vector,
            tentative_state,
            safety_result,
        )
    return RequestResult(
        "WAIT",
        "The tentative allocation is unsafe; the request is not committed.",
        process_id,
        request_vector,
        tentative_state,
        safety_result,
    )


def format_vector(values: Sequence[int]) -> str:
    return "(" + ", ".join(str(value) for value in values) + ")"


def format_flags(process_ids: Sequence[str], flags: Sequence[bool]) -> str:
    return "[" + ", ".join(
        f"{process_id}={'True' if flag else 'False'}"
        for process_id, flag in zip(process_ids, flags)
    ) + "]"


def print_state_summary(state: BankerState) -> None:
    print("\nSYSTEM STATE")
    print("Resources:", ", ".join(state.resource_ids))
    print("Total:", format_vector(state.total))
    print("Allocation totals:", format_vector(state.allocated_total))
    print("Available = Total - Allocation totals:", format_vector(state.available))
    print("Need = Max - Allocation")
    header = f"{'Process':<10}{'Allocation':<22}{'Max':<22}Need"
    print(header)
    print("-" * len(header))
    for index, process_id in enumerate(state.process_ids):
        print(
            f"{process_id:<10}{format_vector(state.allocation[index]):<22}"
            f"{format_vector(state.maximum[index]):<22}"
            f"{format_vector(state.need[index])}"
        )


def print_safety_result(state: BankerState, result: SafetyResult) -> None:
    print("\nSAFETY TRACE")
    print("Initial Work = Available =", format_vector(state.available))
    print("Initial Finish =", format_flags(state.process_ids, (False,) * len(state.process_ids)))
    last_pass = 0
    for event in result.events:
        if event.pass_number != last_pass:
            last_pass = event.pass_number
            print(f"\nPass {last_pass}")
        outcome = "PASS" if event.can_finish else "FAIL"
        print(
            f"  Need[{event.process_id}] {format_vector(event.need)} <= "
            f"Work {format_vector(event.work_before)} -> {outcome}"
        )
        if event.can_finish:
            print(
                f"  {event.process_id} finishes; releases "
                f"{format_vector(event.allocation_released or ())}"
            )
            print("  Work =", format_vector(event.work_after or ()))
            print("  Finish =", format_flags(state.process_ids, event.finish_after))

    if result.safe:
        print("\nSTATE: SAFE")
        print("Safe sequence:", " -> ".join(result.safe_sequence))
    else:
        unfinished = [
            process_id
            for process_id, finished in zip(state.process_ids, result.finish)
            if not finished
        ]
        print("\nNo unfinished process can run with the current Work vector.")
        print("STATE: UNSAFE")
        print("No safe sequence found. Unfinished:", ", ".join(unfinished))
    print("Final Finish =", format_flags(state.process_ids, result.finish))


def print_request_result(state: BankerState, result: RequestResult) -> None:
    print("\nRESOURCE REQUEST")
    print(f"Process: {result.process_id}")
    print("Request:", format_vector(result.request))
    process_index = state.process_ids.index(result.process_id)
    print(
        f"Request <= Need[{result.process_id}] {format_vector(state.need[process_index])}: "
        f"{'YES' if vector_leq(result.request, state.need[process_index]) else 'NO'}"
    )
    print(
        f"Request <= Available {format_vector(state.available)}: "
        f"{'YES' if vector_leq(result.request, state.available) else 'NO'}"
    )
    print("Decision:", result.status)
    print("Reason:", result.reason)
    if result.tentative_state is not None and result.safety_result is not None:
        print_state_summary(result.tentative_state)
        print_safety_result(result.tentative_state, result.safety_result)
    elif result.status == "WAIT":
        print("Available:", format_vector(state.available))


def _read_integer(prompt: str, minimum: int = 0) -> int:
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise InputError("Enter a whole number.") from error
    if value < minimum:
        raise InputError(f"Enter a value of at least {minimum}.")
    return value


def _read_values(prompt: str, count: int, label: str) -> Tuple[int, ...]:
    raw = input(prompt).replace(",", " ").split()
    if len(raw) != count:
        raise InputError(f"Enter exactly {count} {label} value(s).")
    try:
        values = tuple(int(value) for value in raw)
    except ValueError as error:
        raise InputError(f"{label} values must be whole numbers.") from error
    BankerState._validate_nonnegative(values, label)
    return values


def read_state() -> BankerState:
    process_count = _read_integer("Number of processes: ", minimum=1)
    resource_raw = input("Resource labels (for example A B C): ").replace(",", " ").split()
    if not resource_raw:
        raise InputError("Enter at least one resource label.")
    resource_ids = tuple(resource_raw)
    process_ids = tuple(f"P{index}" for index in range(process_count))
    resource_count = len(resource_ids)
    total = _read_values(
        f"Total vector ({resource_count} values): ", resource_count, "Total"
    )

    allocation_rows = []
    print("Enter Allocation rows in process order P0, P1, ...")
    for process_id in process_ids:
        allocation_rows.append(
            _read_values(
                f"Allocation for {process_id}: ", resource_count, "Allocation"
            )
        )

    maximum_rows = []
    print("Enter Max rows in process order P0, P1, ...")
    for process_id in process_ids:
        maximum_rows.append(
            _read_values(f"Max for {process_id}: ", resource_count, "Max")
        )

    return BankerState(
        process_ids=process_ids,
        resource_ids=resource_ids,
        total=total,
        allocation=tuple(allocation_rows),
        maximum=tuple(maximum_rows),
    )


def run_cli() -> None:
    print("BANKER'S ALGORITHM SIMULATOR - FLEISCHER'S FINEST FIVE, PT 101 TOPIC 5")
    while True:
        print("\nMAIN MENU")
        print("1. Run the Safety Algorithm")
        print("2. Check a resource request (extension)")
        print("0. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye.")
            return
        if choice not in {"1", "2"}:
            print("Choose 1, 2, or 0.")
            continue

        try:
            state = read_state()
            print_state_summary(state)
            if choice == "1":
                print_safety_result(state, check_safety(state))
            else:
                process_number = _read_integer(
                    f"Requesting process number (0-{len(state.process_ids) - 1}): ",
                    minimum=0,
                )
                request = _read_values(
                    f"Request vector ({len(state.resource_ids)} values): ",
                    len(state.resource_ids),
                    "Request",
                )
                print_request_result(
                    state, check_request(state, process_number, request)
                )
        except InputError as error:
            print("Input error:", error)


if __name__ == "__main__":
    run_cli()
