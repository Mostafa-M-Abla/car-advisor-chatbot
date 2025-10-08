import os
import sys
import time
from langsmith import Client
from typing_extensions import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langsmith import traceable

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "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"  #TODO
os.environ["OPENAI_API_KEY"] = "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"  #TODO


llm = ChatOpenAI(model="gpt-4o", temperature=1)

# Add decorator so this function is traced in LangSmith
@traceable()
def rag_bot(question: str) -> dict:
    """
    Integrates with the existing car chatbot system to answer questions.

    Args:
        question: User's question about cars

    Returns:
        dict: Contains 'answer' and 'documents' (empty list for compatibility)
    """
    import sys
    import os

    # Add the project root to the path so we can import the chatbot modules
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        # Import the CarChatbot class
        from chatbot.car_chatbot import CarChatbot

        # Initialize the chatbot with the correct config path
        config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")
        chatbot = CarChatbot(config_path=config_path)

        # Process the question and get the response
        answer = chatbot.process_message(question)

        # Return in the expected format
        return {"answer": answer, "documents": []}

    except Exception as e:
        # Fallback response in case of errors
        error_message = f"I encountered an error while processing your question: {str(e)}"
        return {"answer": error_message, "documents": []}




client = Client()

# Define the examples for the dataset
examples = [
    {
        "inputs": {"question": "What is the cheapest car?"},
        "outputs": {"answer": "The cheapest car in Egypt would be the Nissan sunny Manual/ Baseline. It costs 645000 EGP"},
    },
    {
        "inputs": {"question": "Is BMW a korean brand?"},
        "outputs": {"answer": "No, BMW is a German brand."},
    },
    {
        "inputs": {"question": "I want to buy a good car"},
        "outputs": {"answer": "Great! I can help you with that, could you please tell me more about the car you need. e.g. budget, body type or other features that you are looking for?"},
    },
    {
        "inputs": {"question": "What is the cheapest non chinese car with automatic transmission and ESP?"},
        "outputs": {"answer": "The cheapest non chinese car with automatic transmission and ESP will be the Nissan Sunny 2025 Automatic / Baseline"},
    },
    {
        "inputs": {"question": "table"},
        "outputs": {"answer": "Sorry I didn't understand your request. I am an AI chatbot that can help you select a car in the egyptian market, Could you tell me about your budget and the type of car you are looking for?"},
    },
    {
        "inputs": {"question": "What is the cheapest german crossover with panoramic sunroof"},
        "outputs": {
            "answer": "The cheapest crossover with panoramic sunroof is the Opel Crossland A/T / Top Line"},
    },
    {
        "inputs": {"question": "In one sentence tell me which is a more reliable car, corolla or elantra?"},
        "outputs": {
            "answer": "The Corolla is generally considered more reliable than the Elantra."},
    },
    {
        "inputs": {"question": "In one sentence: Which car sells smore in egypt mercedes or elantra?"},
        "outputs": {
            "answer": "Probably Elantra sells more than Meredes"},
    },
    {
        "inputs": {"question": "Which brand provides better service in egypt Hyundai or Fiat"},
        "outputs": {
            "answer": "Hyundai provides better service in egypt"},
    },
    {
        "inputs": {"question": "List the cheapest 5 car sedan models in egypt that are non chinese and are not manual"},
        "outputs": {
            "answer": "1- proton saga 2- Nissan sunny 3- Renault Taliant 4- Mitsubishi Attrage 5- Chevrolet Optra"},
    },
    {
        "inputs": {"question": "Good Car"},
        "outputs": {
            "answer": "Sorry, the request is not clear. I am an AI chatbot that can help you select a car in the egyptian market, Could you tell me about your budget and the type of car you are looking for?"},
    },
    {
        "inputs": {"question": "I want the cheapest electric car with at least 500 km range"},
        "outputs": {
            "answer": "Chery EQ7 2026 Automatic has a range of 520 km and costs 1599000 EGP"},
    },
    {
        "inputs": {"question": "What is the range of the Zeekr X Longrange?"},
        "outputs": {
            "answer": "the range is about 440 km"},
    },
    {
        "inputs": {"question": "How many CC does the Elantra's engine have?"},
        "outputs": {
            "answer": "In Egypt the ELantra's Engine has 1600 cc"},
    },
    {
        "inputs": {"question": "I want an automatic cross over from a european manufacturer that is under 500000 EGP?"},
        "outputs": {
            "answer": "No cars found with those specifications and price in the egyptian market, would you consider relaxing some of the constraints, for example increase your budget or remove the country of origin or body type constraint?"},
    },
    {
        "inputs": {"question": "Suggest me 2 electric car from a reputable brand that has at least 600km of battery range and is below 4.5 m LE"},
        "outputs": {
            "answer": "I suggest one of the follwoing cars: Ioniq 6, Volove EX30, smart-3"},
    },
]


# Create or update the dataset and examples in LangSmith
dataset_name = "Car Selector Chatbot Evaluation Dataset"

# Check if dataset already exists
try:
    dataset = client.read_dataset(dataset_name=dataset_name)
    print(f"Dataset '{dataset_name}' already exists. Updating examples...")

    # Delete existing examples
    existing_examples = list(client.list_examples(dataset_id=dataset.id))
    for example in existing_examples:
        client.delete_example(example.id)
    print(f"Deleted {len(existing_examples)} existing examples.")

except Exception:
    # Dataset doesn't exist, create it
    print(f"Creating new dataset '{dataset_name}'...")
    dataset = client.create_dataset(dataset_name=dataset_name)

# Sort examples alphabetically by question (input)
sorted_examples = sorted(examples, key=lambda x: x["inputs"]["question"].lower())
print(f"Sorted {len(sorted_examples)} examples alphabetically by question.")

# Add the sorted examples
client.create_examples(
    dataset_id=dataset.id,
    examples=sorted_examples
)
print(f"Added {len(sorted_examples)} examples to dataset.")




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





def target(inputs: dict) -> dict:
    return rag_bot(inputs["question"])

# Custom wrapper to add delay between evaluations
evaluation_count = 0
def target_with_delay(inputs: dict) -> dict:
    global evaluation_count

    # Add 10 second delay between examples (but not before the first one)
    if evaluation_count > 0:
        print(f"\n⏳ Waiting 10 seconds before next evaluation...\n")
        time.sleep(10)

    evaluation_count += 1
    print(f"🔄 Evaluating example {evaluation_count}...")

    return rag_bot(inputs["question"])

experiment_results = client.evaluate(
    target_with_delay,
    data=dataset_name,
    evaluators=[correctness],
    experiment_prefix="rag-doc-relevance",
    metadata={"version": "Agentic architecture with function calling"},
)

# Explore results locally as a dataframe if you have pandas installed
# experiment_results.to_pandas()