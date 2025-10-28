# Egyptian Car Market AI Chatbot 🚗

An AI-powered chatbot hat helps users find new cars that suit their preferences — such as body type, brand, and features. The chatbot is equipped with a database of new cars available in Egypt, which was developed as part of this project.

Try the project live at [mostafaabla.com](https://mostafaabla.com/)

## Tech Stack

LangChain + LangGraph | GPT-4.1 | Gradio | SQLite

## Implementation

The projects involves the following steps:

### 1- Web Scrapping
Collected data about specs and prices of new cars in the egyptian market using webscrapping

### 2- Data procesing
Cleaned teh scrapped data

### 3- Created teh Database
Created and optimized an SQLIte Database where teh information about teh cars are stored

### 4- Chatbot
The Chatbot gets teh user question, decide if it needs to access the database or teh question requires only LLM general knowledge. If the question needs data from teh database the LLm access the database using a database tool. The LLM gets teh results, formulate the response and give it back to the user.

The Chatbot uses LangChain/LangGraph agentic architecture with GPT-4.1 as the LLM.

### 5- Evaluation and Hyperparameter tuning
An Evaluation set was developed to evaluate the performance of the chatbot using LangSmith and a hyperparameter tuning for two parameters was performed.

### 6- User Interface
Created a a user interface using Gradio


## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Opens at `http://localhost:7860`


