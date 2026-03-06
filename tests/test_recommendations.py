from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.contact import Contact
from app.services.recommendations import compute_next_actions


def test_next_actions_outreach_when_no_interactions():
    c = Contact(user_id="u", full_name="A", email="a@example.com")
    c.id = "c1"
    c.last_interaction_at = None
    actions = compute_next_actions([c])
    assert actions[0].contact_id == "c1"
    assert actions[0].action == "outreach"


def test_next_actions_follow_up_when_old():
    c = Contact(user_id="u", full_name="B", email="b@example.com")
    c.id = "c2"
    c.last_interaction_at = datetime.now(timezone.utc) - timedelta(days=10)
    actions = compute_next_actions([c])
    assert len(actions) == 1
    assert actions[0].action == "follow_up"

