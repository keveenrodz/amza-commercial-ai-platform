from __future__ import annotations

from pydantic import BaseModel

from core.entities.agent import Agent


class AgentResponse(BaseModel):
    id: str
    name: str
    system_prompt: str
    escalation_rules: str
    model: str

    @classmethod
    def from_domain(cls, agent: Agent) -> AgentResponse:
        return cls(
            id=str(agent.id),
            name=agent.name,
            system_prompt=agent.system_prompt,
            escalation_rules=agent.escalation_rules,
            model=agent.model,
        )


class UpdateAgentRequest(BaseModel):
    system_prompt: str
    escalation_rules: str
    model: str
