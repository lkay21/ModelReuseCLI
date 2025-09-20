from apis.hf_client import HFClient
from apis.gemini import prompt_gemini, get_gemini_key
import re


def performance_claims(model_id: str) -> float:
    client = HFClient()
    model_card = client.model_card_text(model_id)
    res = prompt_gemini(f"Read the following model card of a HuggingFaceModel. " \
                    "Evaluate on a float scale of 0 to 1 the claimed performance of the model. " \
                    "Assign 0.33 points if there is benchmarking data present and another 0.33 points if there are testing scores present and another 0.34 for other performance claims." \
                    "The last line of your response must only contain the final score as a float. You may give partial credit on the last point, depending on the extensiveness of the claims." \
                    "Reply only with a float in the format x.xx" \
                    f"{model_card}", get_gemini_key())
    try:
        score = float(res.rstrip())
        return score
    except:
        print("ERROR")
        return 0

