import logging


class IntentClassifier:
    def __init__(self, client, deployment_name: str):
        self.client = client
        self.deployment_name = deployment_name

    def classify(
        self,
        user_question: str,
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": """
            Classify the user prompt as either "simple" or "complex".
            Respond with only one word: simple or complex.
            """
            },
            {
                "role": "user",
                "content": user_question
            }
        ]

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

        classification = response.choices[0].message.content.strip().lower()

        if classification not in ["simple", "complex"]:
            logging.warning(f"Unexpected classification: {classification}")
            return "complex"

        return classification
