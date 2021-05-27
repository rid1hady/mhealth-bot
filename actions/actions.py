from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    EventType,
    FollowupAction,
)

from actions.gmaps_service import GMapsService

ghq_12_slots = [
    "able_concentrate",
    "lost_sleep",
    "feel_useful",
    "capable_make_decision",
    "under_stress",
    "overcome_difficulties",
    "enjoy_activities",
    "face_up_problems",
    "feel_unhappy",
    "lose_confidence",
    "think_as_worthless",
    "feel_happy",
]


class ActionShowGhqResult(Action):
    def name(self):
        return "action_show_ghq_result"

    def get_score(self, tracker: Tracker) -> int:
        score = sum([tracker.get_slot(key) for key in ghq_12_slots])
        return score

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        score = self.get_score(tracker)
        severity_index = score // 4 if score % 4 != 0 else (score // 4) - 1
        score = (
            f"Berdasarkan jawaban yang kamu berikan, skormu adalah {score} dari 12.\n"
        )
        dispatcher.utter_message(text=score)
        if severity_index == 0:
            dispatcher.utter_message(response="utter_good_condition_user")
            dispatcher.utter_message(response="utter_anything_else")
        elif severity_index == 1:
            dispatcher.utter_message(response="utter_medium_condition_user")
            dispatcher.utter_message(response="utter_pre_mental_health_practice")
            dispatcher.utter_message(response="utter_self_mental_health_practice")
            dispatcher.utter_message(response="utter_anything_else")
        else:
            dispatcher.utter_message(response="utter_bad_condition")
            dispatcher.utter_message(response="utter_help_look_experts")
            dispatcher.utter_message(response="utter_ask_affiliation")
        return [SlotSet(slot_name, None) for slot_name in ghq_12_slots]


class ActionResetGHQFormValue(Action):
    def name(self):
        return "action_reset_ghq_form_value"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        return [SlotSet(slot_name, None) for slot_name in ghq_12_slots]


class ActionShowNearestTherapist(Action):
    def name(self):
        return "action_show_nearest_therapist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        gmaps = GMapsService()
        slot_value = tracker.get_slot("location")
        try:
            lat, long = list(map(float, slot_value.split(",")))
        except ValueError:
            lat, long = gmaps.get_geocode_result(slot_value)

        if lat is None or long is None:
            dispatcher.utter_message(response="utter_location_not_found")
            return [SlotSet("location", None), FollowupAction(name="location_form")]
        else:
            results = gmaps.get_places_nearby({"latitude": lat, "longitude": long})
            dispatcher.utter_message(json_message={"locations": results})
            return [SlotSet("location", None)]



class ActionSetAffiliation(Action):
    def name(self) -> Text:
        return "action_set_affiliation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        intent = tracker.latest_message["intent"].get("name")
        if intent == "affirm":
            return [SlotSet("is_itb_student", True)]
        elif intent == "deny":
            return [SlotSet("is_itb_student", False)]
        return []