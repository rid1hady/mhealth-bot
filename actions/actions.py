from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import random


def get_score(tracker, slots):
    score = sum([tracker.get_slot(key) for key in slots])
    return score


class ActionShowGhqResult(Action):
    def name(self):
        return "action_show_ghq_result"

    @staticmethod
    def get_negative_phrased_slots() -> [Text]:
        return [
            "lost_sleep",
            "under_stress",
            "overcome_difficulties",
            "feel_unhappy",
            "lose_confidence",
            "think_as_worthless"
        ]

    @staticmethod
    def get_positive_phrased_slots() -> [Text]:
        return [
            "able_concentrate",
            "feel_useful",
            "capable_make_decision",
            "enjoy_activities",
            "face_up_problems",
            "feel_happy"
        ]

    @staticmethod
    def get_ghq_slots() -> [Text]:
        phq_slots = [
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
        # To ensure variation
        random.shuffle(phq_slots)
        return phq_slots

    @staticmethod
    def get_severity(score) -> Text:
        severity_index = {
            0: "Secara umum sehat, pertahankan ya.",
            1: "Secara umum kurang sehat, lebih baik jika dilakukan test lebih lanjut.",
            2: '''Secara umum kondisi kesehatan mental kamu bisa dibilang tidak baik-baik saja.
            Aku sangat menyarankan kamu agar menemui psikolog atau psikiater agar 
            segera ditangani lebih baik.'''
        }
        if score == 12:
            return severity_index[2]
        else:
            return severity_index[score // 4]

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        score = get_score(tracker, self.get_ghq_slots())
        severity_comment = self.get_severity(score)
        comment = f"Berdasarkan jawaban kamu, skor kamu adalah {score} dari 12.\n{severity_comment}"
        dispatcher.utter_message(comment)
        return []


class ActionShowPhqResult(Action):
    def name(self):
        return "action_show_phq_result"

    @staticmethod
    def get_phq_slots():
        return [
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

    @staticmethod
    def get_severity(score):
        severity_index = {
            0: "Minimal",
            1: "Ringan",
            2: "Sedang",
            3: "Lumayan parah",
            4: "Parah"
        }
        rounded_score = score // 5
        if rounded_score == 5:
            return severity_index[4]
        else:
            return severity_index[rounded_score]

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        score = get_score(tracker, self.get_phq_slots())
        severity = self.get_severity(score)
        dispatcher.utter_message(f"Skor test kamu terhadap depresi adalah {score}.\n"
                                 f"Kamu tergolong ke dalam {severity}")
        return []


class HandleFurtherTestResult(Action):
    def name(self) -> Text:
        return "handle_further_test_result"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phq_score = get_score(tracker, ActionShowPhqResult.get_phq_slots()) // 5
        rounded_score = phq_score if phq_score < 5 else 4
        check_affiliation = False
        if rounded_score == 0:
            dispatcher.utter_message(template='utter_root_for_user')
        elif 1 <= rounded_score <= 2:
            dispatcher.utter_message(template='utter_self_mental_health_practice')
        else:
            dispatcher.utter_message(template='utter_bad_condition')
            check_affiliation = True
        return [SlotSet("check_affiliation", check_affiliation)]
