from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

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

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        score = self.get_score(tracker)
        severity_index = self.get_severity_index(score)
        score = f"Berdasarkan jawaban yang kamu berikan, skormu adalah {score} dari 12.\n"
        dispatcher.utter_message(score)
        if severity_index == 0:
            dispatcher.utter_message(response='utter_good_condition_user')
            dispatcher.utter_message(response='utter_anything_else')
        elif severity_index == 1:
            dispatcher.utter_message(response='utter_medium_condition_user')
            dispatcher.utter_message(response='utter_self_mental_health_practice')
            dispatcher.utter_message(response='utter_anything_else')
        else:
            dispatcher.utter_message(response='utter_bad_condition')
            dispatcher.utter_message(response='utter_ask_affiliation')
        return [SlotSet(slot_name, None) for slot_name in self.get_slots()]


class ActionShowNearestTherapist(Action):
    def name(self):
        return "action_show_nearest_therapist"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lat, long = [None, None]
        gmaps = GMapsService()
        slot_value = tracker.get_slot('location')
        try:
            lat, long = list(map(float, slot_value.split(',')))
        except ValueError:
            lat, long = gmaps.get_geocode_result(slot_value)
            print(lat, long)

        if lat == None or long == None:
            dispatcher.utter_message(response='utter_location_not_found')
            return [SlotSet('location', None), FollowupAction(name='location_form')]
        else:
            results = gmaps.get_places_nearby({'latitude': lat, 'longitude': long})
            dispatcher.utter_message(json_message = {'locations': results})
            return [SlotSet('location', None)]
