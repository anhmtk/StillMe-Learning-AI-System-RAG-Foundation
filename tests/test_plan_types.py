from stillme_core.plan_types import PlanItem


def test_plan_item_defaults():
    p = PlanItem(id="1", title="Fix typo")
    assert p.action == "edit_file"
    assert p.risk == "low"
    assert p.tests_to_run == []
    assert p.deps == []
