from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import List, Optional

from app.models.contact import Contact
from app.schemas.actions import NextActionOut


@dataclass
class Heuristics:
    follow_up_days: int = 5


def compute_relationship_strength(
    last_interaction_at: Optional[datetime],
    interaction_count: int,
    now: Optional[datetime] = None,
) -> float:
    if last_interaction_at is None or interaction_count <= 0:
        return 0.0

    now = now or datetime.now(timezone.utc)
    if last_interaction_at.tzinfo is None:
        last_interaction_at = last_interaction_at.replace(tzinfo=timezone.utc)

    days_since = max(0.0, (now - last_interaction_at).total_seconds() / 86400.0)
    recency = math.exp(-days_since / 14.0)
    frequency = min(1.0, math.log1p(interaction_count) / math.log1p(10.0))
    strength = (0.7 * recency) + (0.3 * frequency)
    return round(float(strength), 3)


def compute_next_actions(
    contacts: List[Contact], heuristics: Optional[Heuristics] = None
) -> List[NextActionOut]:
    heuristics = heuristics or Heuristics()
    now = datetime.now(timezone.utc)
    actions: List[NextActionOut] = []

    for contact in contacts:
        if contact.last_interaction_at is None:
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="outreach",
                    reason="No interactions yet",
                    due_at=now,
                    relationship_strength=0.0,
                )
            )
            continue

        # Simple follow-up heuristic: if last interaction is older than follow_up_days.
        if contact.last_interaction_at < now - timedelta(days=heuristics.follow_up_days):
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="follow_up",
                    reason=f"Last interaction > {heuristics.follow_up_days} days ago",
                    due_at=contact.last_interaction_at + timedelta(days=heuristics.follow_up_days),
                    relationship_strength=compute_relationship_strength(
                        contact.last_interaction_at, interaction_count=1, now=now
                    ),
                )
            )

    actions.sort(key=lambda a: (a.due_at is None, a.due_at))
    return actions
