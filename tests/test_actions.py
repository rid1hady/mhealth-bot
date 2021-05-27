import pytest
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    EventType,
    FollowupAction,
)
from actions import actions

@pytest.mark.parametrize(
    "intent, expected_events",
    [
        ("affirm", [SlotSet("is_itb_student", True)]),
        ("deny", [SlotSet("is_itb_student", False)]),
        ("other", []),
    ],
)
def test_action_set_affiliation(
    tracker: Tracker,
    dispatcher: CollectingDispatcher,
    domain: Dict[Text, Any],
    intent: Text,
    expected_events: List[EventType],
):
    tracker.latest_message["intent"]["name"] = intent
    action = actions.ActionSetAffiliation()
    actual_events = action.run(dispatcher, tracker, domain)
    assert actual_events == expected_events

base_info = {
    "able_concentrate": True,
    "feel_useful": True,
    "capable_make_decision":True,
    "enjoy_activities": True,
    "face_up_problems": True,
    "feel_happy": True,
    "lost_sleep": True,
    "under_stress": True,
    "overcome_difficulties": True,
    "feel_unhappy": True,
    "lose_confidence": True,
    "think_as_worthless": True
}

@pytest.mark.parametrize(
    "collected_info, expected_len, expected_messages, expected_score",
    [
        (
          {
            **base_info,
            "face_up_problems": False,
            "feel_happy": False,
            "lost_sleep": False,
            "under_stress": False,
            "overcome_difficulties": False,
            "feel_unhappy": False,
            "lose_confidence": False,
            "think_as_worthless": False,
          },
          3,
          [
            "utter_good_condition_user",
            "utter_anything_else"
          ],
          4
        ),
        (
          {
            **base_info,
            "face_up_problems": False,
            "feel_happy": False,
            "overcome_difficulties": False,
            "feel_unhappy": False,
            "lose_confidence": False,
            "think_as_worthless": False,
          },
          4,
          [
            "utter_medium_condition_user",
            "utter_self_mental_health_practice",
            "utter_anything_else"
          ],
          6
        ),
        (
          {
            **base_info
          },
          4,
          [
            "utter_bad_condition",
            "utter_help_look_experts",
            "utter_ask_affiliation"
          ],
          12
        )
    ],
)
def test_action_show_ghq_result(
    tracker: Tracker,
    dispatcher: CollectingDispatcher,
    domain: Dict[Text, Any],
    collected_info: Dict[Text, bool],
    expected_len: int,
    expected_messages: List[Text],
    expected_score: int
):
    tracker.slots.update(collected_info)
    action = actions.ActionShowGhqResult()
    actual_events = action.run(dispatcher, tracker, domain)
    assert actual_events == [SlotSet(slot_name, None) for slot_name in collected_info.keys()]
    assert len(dispatcher.messages) == expected_len
    expected_score_message = (
        f"Berdasarkan jawaban yang kamu berikan, skormu adalah {expected_score} dari 12.\n"
    )
    assert dispatcher.messages[0]["text"] == expected_score_message
    messages = [m["response"] for m in dispatcher.messages[1:]]
    assert messages == expected_messages
