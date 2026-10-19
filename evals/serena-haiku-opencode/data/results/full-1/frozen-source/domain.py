from dataclasses import dataclass
from typing import Literal

from vendor.capture import Candidate
from vendor.domain import TaskSpec

Effort = Literal['medium', 'high']
Arm = Literal['native', 'serena']
Role = Literal['exploration', 'implementation']

@dataclass(frozen=True)
class Configuration:
    effort: Effort
    arm: Arm

    @property
    def id(self):
        return f'haiku-{self.effort}-{self.arm}'

    @property
    def candidate(self):
        return Candidate(f'haiku-{self.effort}', 'cli_proxy', 'cpa-claude-haiku-5-5', self.effort,
                         'cli_proxy', 'http://127.0.0.1:8317/v1', self.effort, False,
                         'claude-haiku-5-5', 'messages', 'key')

@dataclass(frozen=True)
class ExplorationCase:
    id: str

    @property
    def role(self):
        return 'exploration'

@dataclass(frozen=True)
class ImplementationCase:
    task: TaskSpec

    @property
    def id(self):
        return self.task.id

    @property
    def role(self):
        return 'implementation'

Case = ExplorationCase | ImplementationCase
CONFIGURATIONS = tuple(Configuration(effort, arm) for effort in ('medium', 'high') for arm in ('native', 'serena'))
LIMITS = {'exploration': {'seconds': 300, 'steps': 25, 'calls': None},
          'implementation': {'seconds': 1200, 'steps': None, 'calls': 60}}
TOOLS = (
    ('initial_instructions', False, False),
    ('get_symbols_overview', False, True),
    ('find_symbol', False, True),
    ('find_referencing_symbols', False, True),
    ('search_for_pattern', False, True),
    ('get_diagnostics_for_file', False, True),
    ('replace_symbol_body', True, True),
    ('insert_before_symbol', True, True),
    ('insert_after_symbol', True, True),
)

def mcp_tools(role):
    return tuple(name for name, editing, useful in TOOLS if role == 'implementation' or not editing)

def native_tools(role):
    return ('read', 'glob', 'grep', 'list') if role == 'exploration' else ('terminal',)

def allowed_tools(role, arm):
    return (*native_tools(role), *(f'serena_{name}' for name in mcp_tools(role))) if arm == 'serena' else native_tools(role)

def useful_mcp(name):
    return any(name == tool and useful for tool, editing, useful in TOOLS)
