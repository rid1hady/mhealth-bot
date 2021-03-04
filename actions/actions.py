from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction

class AnamnesisForm(FormAction):
    def name(self):
        return "anamnesis_form"

    @staticmethod
    def required_slots(tracker):
        # TODO: Add conditional checking on questionaire type
        phq_slots = [
            "interest_condition",
            "sadness_condition",
            "sleep_condition",
            "diet_condition",
            "energy_condition",
            "optimism_condition",
            "concentration_condition",
            "movement_condition",
            "suicide_thought_condition"
        ]
        return phq_slots

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "suicide_thought": [
                self.from_text(intent="inform"),
            ],
        }

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        dispatcher.utter_message("Thanks, great job!")
        return []

