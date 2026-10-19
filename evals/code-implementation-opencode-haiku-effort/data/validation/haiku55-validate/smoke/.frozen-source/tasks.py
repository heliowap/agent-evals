from dataclasses import replace
from contract import REQUEST
from domain import TaskSpec
from tasks_python import TASKS as PYTHON_TASKS
from tasks_typescript import TASKS as TYPESCRIPT_TASKS


TASKS = tuple(
    replace(task, id="py-money-contract-v2", request=REQUEST,
            files={**task.files, "README.md": task.files["README.md"].replace(task.request, REQUEST)})
    if task.id == "py-money-contract" else task
    for task in PYTHON_TASKS + TYPESCRIPT_TASKS
)
SMOKE = TaskSpec(
    "smoke", "smoke", "smoke", "python",
    "Add clamp(value, lower, upper) to src/numbers.py. It returns value within the inclusive bounds, lower below them and upper above them. Reject lower > upper with ValueError. Preserve add. Add checks and run python3 checks/public.py. Change only src/ and checks/.",
    {"src/__init__.py": "", "src/numbers.py": "def add(left, right):\n    return left + right\n",
     "checks/public.py": "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path.cwd()))\nfrom src.numbers import add\nassert add(2, 3) == 5\n",
     "README.md": "Run python3 checks/public.py. Source changes belong in src/ and checks/.\n"},
    {"src/numbers.py": "def add(left, right):\n    return left + right\n\ndef clamp(value, lower, upper):\n    if lower > upper:\n        raise ValueError('invalid bounds')\n    return min(upper, max(lower, value))\n"},
    "from src.numbers import clamp\nassert clamp(-5, 0, 10) == 0\nassert clamp(15, 0, 10) == 10\nassert clamp(5, 0, 10) == 5\nassert clamp(7, 7, 7) == 7\ntry:\n    clamp(0, 2, 1)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('invalid bounds accepted')\n",
    ("src/", "checks/"),
)
BUDGET_TASK = TaskSpec(
    "budget-proof", "budget", "cancellation", "python",
    "Inspect src/numbers.py and checks/public.py using the terminal. Keep reading the project files with additional terminal calls until the operator stops the session. Do not send a final answer or modify files. This task intentionally remains active.",
    SMOKE.files, {}, "assert True\n", ("src/", "checks/"),
)


def inventory(phase):
    if phase == "smoke":
        return (SMOKE,)
    if phase == "budget":
        return (BUDGET_TASK,)
    return tuple(task for task in TASKS if task.phase == phase)
