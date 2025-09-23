from apis.hf_client import HFClient
from apis.gemini import prompt_gemini, get_gemini_key
import re


def performance_claims(model_id: str) -> float:
    client = HFClient()
    model_card = client.model_card_text(model_id)
    res = prompt_gemini(f"Read the following model card of a HuggingFaceModel. " \
                    "Evaluate on a float scale of 0 to 1 the claimed performance of the model. " \
                    "Assign 0.33 points if there is benchmarking data present " \
                    "and another 0.33 points if there are testing scores present "\
                    ", add another 0.1 points for presence of other performance claims." \
                    "and another 0.24 if the card contains specific and data-backed claims (partial credit is allowed for this 0.24)" \
                    "The last line of your response must only contain the final score as a float." \
                    "Reply only with a float in the format x.xx" \
                    f"{model_card}", get_gemini_key())
    try:
        score = float(res.rstrip())
        return score
    except:
        print("ERROR")
        return 0

