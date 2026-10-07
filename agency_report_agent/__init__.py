"""Report Desk — drafts an agency's monthly client reports, fact-checks every
figure against the uploaded data, and waits for a person to approve them."""

from .desk import Desk
from .graph import build_graph
from .verify import verify

__all__ = ["Desk", "build_graph", "verify"]
