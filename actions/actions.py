from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

from actions.api.gmaps_service import GMapsService

class ActionShowGhqResult(Action):
    def name(self):
        return "action_show_ghq_result"

    @staticmethod
    def get_slots() -> [Text]:
        return [
            "able_concentrate",
            "feel_useful",
            "capable_make_decision",
            "enjoy_activities",
            "face_up_problems",
            "feel_happy",
            "lost_sleep",
            "under_stress",
            "overcome_difficulties",
            "feel_unhappy",
            "lose_confidence",
            "think_as_worthless"
        ]

    def get_score(self, tracker: Tracker) -> int:
        score = sum([tracker.get_slot(key) for key in self.get_slots()])
        return score

    @staticmethod
    def get_severity_index(score: int) -> Text:
        return 4 if (score == 12) else score // 4

    @staticmethod
    def get_next_action(dispatcher: CollectingDispatcher, severity_index: int) -> List[Dict[Text, Any]]:
        check_affiliation = False
        if severity_index == 0:
            dispatcher.utter_message(template='utter_good_condition_user')
            dispatcher.utter_message(template='utter_anything_else')
        elif severity_index == 1:
            dispatcher.utter_message(template='utter_medium_condition_user')
            dispatcher.utter_message(template='utter_self_mental_health_practice')
            dispatcher.utter_message(template='utter_anything_else')
        else:
            dispatcher.utter_message(template='utter_bad_condition')
            dispatcher.utter_message(template='utter_ask_affiliation')
        return []

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        score = self.get_score(tracker)
        severity_index = self.get_severity_index(score)
        score = f"Berdasarkan jawaban yang kamu berikan, skormu adalah {score} dari 12.\n"
        dispatcher.utter_message(score)
        return self.get_next_action(dispatcher, severity_index)


class ActionShowNearestTherapist(Action):
    def name(self):
        return "action_show_nearest_therapist"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lat, long = list(map(float, tracker.get_slot('location').split(',')))
        gmaps = GMapsService()
        results = gmaps.get_places_nearby({'latitude': lat, 'longitude': long})
        dispatcher.utter_message(json_message = {'locations': results})
        return []
