"""Agency Report Agent — a LangGraph agent that drafts, self-checks, and
routes monthly marketing reports for approval."""

from .graph import build_graph

__all__ = ["build_graph"]
