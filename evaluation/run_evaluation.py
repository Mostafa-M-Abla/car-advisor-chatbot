import os
from langsmith import Client
from typing_extensions import Annotated, TypedDict
from langchain_openai import ChatOpenAI
import os
from langchain_openai import ChatOpenAI
from langsmith import traceable

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "YOUR LANGSMITH API KEY"   #TODO
os.environ["OPENAI_API_KEY"] = "YOUR OPENAI API KEY"  #TODO


#TODO #TODO #TODO    #TODO
llm = ChatOpenAI(model="gpt-4o", temperature=1)

# Add decorator so this function is traced in LangSmith
@traceable()
def rag_bot(question: str) -> dict:
    # LangChain retriever will be automatically traced
    docs = retriever.invoke(question)
    docs_string = "".join(doc.page_content for doc in docs)
    instructions = f"""You are a helpful assistant who is good at analyzing source information and answering questions.
       Use the following source documents to answer the user's questions.
       If you don't know the answer, just say that you don't know.
       Use three sentences maximum and keep the answer concise.

Documents:
{docs_string}"""
    # langchain ChatModel will be automatically traced
    ai_msg = llm.invoke([
            {"role": "system", "content": instructions},
            {"role": "user", "content": question},
        ],
    )
    return {"answer": ai_msg.content, "documents": docs}




client = Client()

# Define the examples for the dataset
examples = [
    {
        "inputs": {"question": "What is the cheapest car?"},
        "outputs": {"answer": "the cheapest car in Egypt would be the Nissan sunny Manual/ Baseline. It costs 645000 EGP"},
    },
    {
        "inputs": {"question": "Is BMW a korean brand?"},
        "outputs": {"answer": "No, BMW is a German brand."},
    },
    {
        "inputs": {"question": "I want to buy a good car"},
        "outputs": {"answer": "Great! i can help you with that, could you please tell me more about the car you need. e.g. budget, body type or other features that you are looking for?"},
    },
    {
        "inputs": {"question": "What is the cheapest non chinese car with automatic transmission and ESP?"},
        "outputs": {"answer": "The cheapest non chinese car with automatic transmission and ESP will be the Nissan Sunny 2025 Automatic / Baseline"},
    },
    {
        "inputs": {"question": "table"},
        "outputs": {"answer": "Sorry I didn't understand your request. I am AI chatbot that can help you select a car in the egyptian market, Could you tell me about yopur budget and the type of car you are looking for?"},
    }
]


# Create the dataset and examples in LangSmith
dataset_name = "Car Selector Chatbot Evaluation Dataset"
dataset = client.create_dataset(dataset_name=dataset_name)
client.create_examples(
    dataset_id=dataset.id,
    examples=examples
)




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

experiment_results = client.evaluate(
    target,
    data=dataset_name,
    evaluators=[correctness],
    experiment_prefix="rag-doc-relevance",
    metadata={"version": "LCEL context, gpt-4-0125-preview"},
)

# Explore results locally as a dataframe if you have pandas installed
# experiment_results.to_pandas()