import os
from langsmith import Client

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