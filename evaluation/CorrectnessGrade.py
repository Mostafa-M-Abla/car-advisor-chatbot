from typing_extensions import Annotated, TypedDict
from langchain_openai import ChatOpenAI
import os

# Grade output schema
class CorrectnessGrade(TypedDict):
    # Note that the order in the fields are defined is the order in which the model will generate them.
    # It is useful to put explanations before responses because it forces the model to think through
    # its final response before generating it:
    explanation: Annotated[str, ..., "Explain your reasoning for the score"]
    correct: Annotated[bool, ..., "True if the answer is correct, False otherwise."]

# Grade prompt
correctness_instructions = """You are evaluator that evaluates the correctness of teh answers for a chatbot that is designed to help user to choose a car. You will be given a QUESTION, the GROUND TRUTH (correct) ANSWER, and the CHATBOT ANSWER. Here is the grade criteria to follow:
(1) Grade the chatbot answers based ONLY on their factual accuracy relative to the ground truth answer. (2) Ensure that the chatbot answer does not contain any conflicting statements.
(3) It is OK if the chatbot answer contains more information than the ground truth answer, as long as it is factually accurate relative to the  ground truth answer. 
(4) If the ground truth has more info than the question asked, then for the chatbot answer to be regarded as correct it is enough to answer the asked question without the additional info in the ground truth answer. E.g. if the question is What is teh cheapest car inj Egypt? and teh grondtruth mention that it is a certain car and list its specs. Then for teh chatbot answer to be regarded as correct then it should at least mention the car model.

Correctness:
A correctness value of True means that the chatbot's answer meets all of the criteria.
A correctness value of False means that the chatbot's answer does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. Avoid simply stating the correct answer at the outset."""

# Grader LLM
grader_llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0,
    api_key=os.getenv('OPENAI_API_KEY')
).with_structured_output(
    CorrectnessGrade, method="json_schema", strict=True
)

def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """An evaluator for RAG answer accuracy"""
    answers = f"""\
QUESTION: {inputs['question']}
GROUND TRUTH ANSWER: {reference_outputs['answer']}
CHATBOT ANSWER: {outputs['answer']}"""
    # Run evaluator
    grade = grader_llm.invoke([
        {"role": "system", "content": correctness_instructions},
        {"role": "user", "content": answers}
    ])
    return grade["correct"]