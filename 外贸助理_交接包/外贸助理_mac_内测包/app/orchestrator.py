from __future__ import annotations

from .action_protocol import ActionExecutor, dedupe_actions, parse_actions
from .capsule_builder import CapsuleBuilder
from .contracts import ActionExecutionResult, CapsuleRequest, ContextCapsule


class TradeAssistantOrchestrator:
    def __init__(self, capsule_builder: CapsuleBuilder, action_executor: ActionExecutor) -> None:
        self.capsule_builder = capsule_builder
        self.action_executor = action_executor

    def build_capsule(self, request: CapsuleRequest) -> ContextCapsule:
        return self.capsule_builder.build(request)

    def parse_actions(self, model_output: str):
        return parse_actions(model_output)

    def execute_actions(self, model_output: str) -> list[ActionExecutionResult]:
        commands = dedupe_actions(parse_actions(model_output))
        return [self.action_executor.run(command) for command in commands]
