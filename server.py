from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import openai
from typing_extensions import override
from openai import AssistantEventHandler
import numpy as np
import json 
import re
import spacy
from scipy import spatial
# from common_english_words import word_list_set
from spellchecker import SpellChecker
import language_tool_python
import os
import requests
from dotenv import load_dotenv



app = Flask(__name__)
CORS(app)  # This is necessary to handle CORS if your Flutter app and this backend are on different domains.

# Load environment variables from the .env file
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

print(f"API Key: {api_key}")
# Initialize LanguageTool for grammar checking
tool = language_tool_python.LanguageTool('es')  # Set to Spanish

# Initialize SpellChecker for Spanish
spell = SpellChecker(language='es')



# Load the spaCy model
nlp = spacy.load('en_core_web_md')
word_list_set = set(nlp.vocab.strings)

class EventHandler(AssistantEventHandler):    
    def __init__(self):
            super().__init__()
            # self.user_progress = user_progress
            self.current_response = ""
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=False)
        self.current_response += delta.value
        
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
    
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

# Then, we use the `stream` SDK helper 
# with the `EventHandler` class to create the Run 
# and stream the response.

def load_elo_samples(file_path):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    with open(file_path, 'r') as file:
        return json.load(file)

def get_random_elo(user_rating, mean=0, std_dev=400):
    random_elo = int(np.random.normal(user_rating, std_dev))
    return max(0, min(2000, random_elo))

# Map ELO to CEFR levels
def elo_to_cefr(elo_rating):
    if 0 <= elo_rating <= 333:
        return "A1"
    elif 334 <= elo_rating <= 666:
        return "A2"
    elif 667 <= elo_rating <= 1000:
        return "B1"
    elif 1001 <= elo_rating <= 1333:
        return "B2"
    elif 1334 <= elo_rating <= 1666:
        return "C1"
    elif 1667 <= elo_rating <= 2000:
        return "C2"
    else:
        return "Unknown"

def load_vocabulary(vocabulary_files):
    vocabulary = []
    for vocab_file in vocabulary_files:
        with open(f'./{vocab_file}', 'r') as file:
            vocabulary.extend(file.read().splitlines())
    return vocabulary






class OpenAIChat:
    def __init__(self, api_key):
        self.users_rating = 300
        self.users_cefr_level = elo_to_cefr(self.users_rating)
        self.topic_to_practice = None
        self.lesson_recommender_tracker = {
            "Present Tense Verbs": 0,
            "Preterite Tense": 0,
            "Imperfect Tense": 0,
            "Future Tense": 0,
            "Conditional Tense": 0,
            "Subjunctive Mood": 0,
            "Reflexive Verbs": 0,
            "Commands (Imperatives)": 0,
            "Possessive Adjectives": 0,
            "Possessive Pronouns": 0,
            "Direct Object Pronouns": 0,
            "Indirect Object Pronouns": 0,
            "Double Object Pronouns": 0,
            "Gustar and Similar Verbs": 0,
            "Ser vs. Estar": 0,
            "Por vs. Para": 0,
            "Comparatives and Superlatives": 0,
            "Demonstrative Adjectives": 0,
            "Demonstrative Pronouns": 0,
            "Interrogative Words": 0,
            "Negative Words": 0,
            "Adverbs": 0,
            "Prepositions": 0,
            "Articles": 0,
            "Gender and Number Agreement": 0,
            "Noun-Adjective Agreement": 0,
            "Sentence Structure": 0,
            "Questions and Exclamations": 0,
            "Passive Voice": 0,
            "Relative Pronouns": 0,
            "Conditional Sentences": 0,
            "Idiomatic Expressions": 0,
            "Numbers": 0,
            "Time Expressions": 0,
            "Conjunctions": 0,
            "Gerunds and Present Participles": 0,
            "Infinitives": 0,
            "Future Perfect": 0,
            "Past Perfect (Pluperfect)": 0,
            "Imperfect Subjunctive": 0
        }
        self.client = OpenAI(api_key=api_key)
        # self.expected_response_client = OpenAI(api_key=api_key)
        self.language = None
        self.assistant = self.client.beta.assistants.retrieve("asst_XDSA4hq7fq8fd0pdtAb0iUTG")
        self.advanced_word_detector_assistant = self.client.beta.assistants.retrieve("asst_gZ5kpgBJaPbWcKz3YrWgmtUk")
        self.english_word_counter_assistant = self.client.beta.assistants.retrieve('asst_QHN8ywHLkU7wLp10G7dgENtT')
        self.response_score_assistant = self.client.beta.assistants.retrieve("asst_HH1NiwYkrgXKoUrNI1sPEQoL")
        self.help_detector_assistant = self.client.beta.assistants.retrieve("asst_qPLbwpxRHY7dnM9G9fewViQk")
        self.mistake_detector_assistant = self.client.beta.assistants.retrieve("asst_NKpMtClPEqj8xHlQ46LM9304")
        self.thread = self.client.beta.threads.create()
        self.advanced_word_detector_thread = self.client.beta.threads.create()
        self.response_score_thread = self.client.beta.threads.create()
        self.english_word_counter_thread = self.client.beta.threads.create()
        self.help_detector_thread = self.client.beta.threads.create()
        self.mistake_detector_thread = self.client.beta.threads.create()
        self.tool = language_tool_python.LanguageTool('es')  # Set to Spanish
        self.spell = SpellChecker(language='es')  # Spanish spell checker
        
        self.user_response = None
        self.bot_response = None
        self.chat_messages = []
        print(f"Thread ID: {self.thread.id}")
        print(f"OpenAI API Version: {openai.__version__}")

    def send_message(self, message):
    
        self.user_response = message

        help_detector_bot_event_handler  = EventHandler()
        with self.client.beta.threads.runs.stream(
            
                thread_id=self.help_detector_thread.id,
                assistant_id=self.help_detector_assistant.id,
                additional_messages=[{"role": "user","content": self.user_response}],
                event_handler= help_detector_bot_event_handler,
        ) as stream:
            stream.until_done()
        response_json = json.loads(help_detector_bot_event_handler.current_response)
        user_asking_for_help = response_json.get('user_asking_for_help', 0)
        print("User is asking for help?:", user_asking_for_help )

        elo_examples = load_elo_samples(f"{self.language}_categories.json")
        new_prompt, difficult_level_of_bot = self.generate_prompt(user_rating=self.users_rating,elo_samples=elo_examples,topic=self.topic_to_practice, is_user_asking_for_help=user_asking_for_help)
        print("topic to practice: ", self.topic_to_practice)
        print("this is current prompt: ", new_prompt)

        additional_instructions = ''
        if not user_asking_for_help:
            additional_instructions = """
                1.) Read your instructions 
                2.) Use your file_search function to look at only the files you are allowed to use the vocabulary from 
                3.) Respond
            """
    
        
        print(new_prompt)
    
        event_handler = EventHandler()
        self.chat_messages.append({"role": "user", "content": message})
        with self.client.beta.threads.runs.stream(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                additional_messages=self.chat_messages,
                instructions=new_prompt,
                additional_instructions=additional_instructions,
                event_handler=event_handler,
        ) as stream:
            stream.until_done()
        self.chat_messages.append({"role": "assistant", "content": event_handler.current_response})




        if self.bot_response is not None and user_asking_for_help != 'yes':
            # mistake_detector_event_handler = EventHandler()
            # with self.client.beta.threads.runs.stream(
            
            #     thread_id=self.mistake_detector_thread.id,
            #     assistant_id=self.mistake_detector_assistant.id,
            #     additional_messages=[{"role": "user","content": self.user_response}],
            #     additional_instructions=additional_instructions,
            #     event_handler= mistake_detector_event_handler,
            # ) as stream:
            #     stream.until_done()
            # mistakes = response_json.get('mistakes', 0)
            # print(mistakes)
            # mistake_types = mistakes.get('mistake_type', 0)
            # print(mistake_types)
            self.calculate_updated_rating(user_response=self.user_response, expected_response=self.bot_response, difficulty_level=difficult_level_of_bot)

        # Set the final bot response
        self.bot_response = event_handler.current_response

        # Return the final bot response
        return self.bot_response, self.users_rating
    
    def update_lesson_recommender_tracker(self, mistakes):
        decay_factor = 0.8
        # When the value of a certain mistake type hits 10, then it will recommend to the uesr that specific lesson
        lessons_to_recommend = []
        for mistake_type in mistakes:
            self.lesson_recommender_tracker[mistake_type] += 1
        for mistake_type in self.lesson_recommender_tracker:
            if self.lesson_recommender_tracker[mistake_type] >= 10:
                lessons_to_recommend.append(mistake_type)
                continue
            self.lesson_recommender_tracker[mistake_type] *= decay_factor
        if len(lessons_to_recommend) >= 1:
            print(lessons_to_recommend)
            print(f' I have noticed that you struggle with this particular concept: {lessons_to_recommend[0]}. I recommend you take a lesson to work on this.')

    

    
    def generate_prompt(self, user_rating, elo_samples, topic, is_user_asking_for_help):
        random_elo = get_random_elo(user_rating)
        self.cefr_level = elo_to_cefr(random_elo)
        vocab_json_file = load_elo_samples(f"{self.language}_categories.json")
        print(random_elo)
        print(self.cefr_level)
        category_data = vocab_json_file.get("General Conversation")
        
        level_data = category_data.get(self.cefr_level)
        

        vocab_files = level_data.get("vocabulary")
        vocabulary_files_str = ", ".join(vocab_files)
        grammar = level_data.get("grammar")

        if is_user_asking_for_help == 'yes':
            return (
            f"You are a helpful assistant for helping the user learn {self.language} through a conversation about {topic}. "
            f"The user currently needs your help in this conversation. Help them with what they need. Make sure your response is in English primarily. Only include {self.language} in the respones if the user asks for a translation or understanding the meaning of a word for instance.", random_elo
            )
        
        else:
        
            return (
                f"You are a helpful assistant for helping the user learn {self.language} through a conversation about {topic}. "
                f"You are only allowed to use vocabulary within {vocabulary_files_str} as well as their conjugations and similar words since you are talking at a {self.cefr_level} level. "
                f"Try to apply these grammar rules in the conversation to help the user learn and get familiar with them: {grammar}. "
                "If the user makes a mistake, let them know in English that they have made a mistake, tell them what their mistake was, and tell them how to fix it. "
                f"If the user types a word in English be sure to tell them the word in {self.language} so they know how to say the word from now on. "
                "Finally, continue the conversation where it left off.", random_elo

            )
        
    def set_chat_topic(self, topic):
        
        self.topic_to_practice = topic
        print("Topic to practice has been set to: ", self.topic_to_practice)
    
    def set_language(self, language):
        self.language = language

    def set_users_rating(self, rating):
        self.users_rating = rating

    def reset_chat(self):

        self.user_response = None
        self.bot_response = None
        self.chat_messages = []
        self.users_rating = None
        
        self.topic_to_practice = None
        # Reset any other stateful attributes here if necessary
        print("Chat has been reset.")
        
    def calculate_advanced_vocab_score(self, user_response, user_cefr_level):
        # Get the vocabulary for levels above the user's current level
        advanced_vocab = self.get_advanced_vocabulary(user_cefr_level)
        # print(advanced_vocab)

        is_in_advanced_vocab = "bien" in advanced_vocab

        # Print the result
        print(is_in_advanced_vocab)  
        
        # Check if user response contains advanced vocabulary
        words = set(re.findall(r'\b\w+\b', user_response.lower()))
        advanced_words = words.intersection(advanced_vocab)
        print("these are the advanced words", advanced_words)
        
        # Calculate the score and scale it to a maximum of 0.5
        advanced_vocab_score = (len(advanced_words) / len(words)) * 0.5 if words else 0
        return advanced_vocab_score


    def get_advanced_vocabulary(self, user_cefr_level):


        additional_instructions = f"""
                1.) Use your file_search function to look at only the CEFR files higher than {self.cefr_level}
                2.) Run the function advanced_word_detector
            """

        return 'advanced word count returned'

        # advanced_word_detector_event_handler = EventHandler()
        # with self.client.beta.threads.runs.stream(
            
        #         thread_id=self.advanced_word_detector_thread.id,
        #         assistant_id=self.advanced_word_detector_assistant.id,
        #         additional_messages=[{"role": "user","content": self.user_response}],
        #         additional_instructions=additional_instructions,
        #         event_handler= advanced_word_detector_event_handler,
                

        # ) as stream:
        #     stream.until_done()
        # response_json = json.loads(advanced_word_detector_event_handler.current_response)
        # print(response_json)
        # number_of_advanced_words = response_json.get('number_of_advanced_words', 0)
        # advanced_words_used = response_json.get('advanced_words_used', 0)
        # print("Number of advanced words used:", number_of_advanced_words )
        # print("Number of advanced words used:", advanced_words_used )
        
        return number_of_advanced_words

    def calculate_response_score(self):

        response_score_event_handler = EventHandler()
        with self.client.beta.threads.runs.stream(
            
                thread_id=self.response_score_thread.id,
                assistant_id=self.response_score_assistant.id,
                additional_messages=[{"role": "user","content": "bot: " + self.bot_response + "user: " + self.user_response}],
                
                event_handler= response_score_event_handler,
        ) as stream:
            stream.until_done()
        response_json = json.loads(response_score_event_handler.current_response)
        response_score = response_json.get('Overall Score', 0)
        print("Response Score:", response_score )
        

        

        self.bot_response = response_score_event_handler.current_response
        return response_score



    def calculate_english_words_score(self, user_response):
        words = re.findall(r'\b\w+\b', user_response.lower())
        print(words)
        if not words:
            return 0
        
        
        def count_english_word(user_response):
            
            
            english_word_counter_event_handler = EventHandler()
            with self.client.beta.threads.runs.stream(
                
                    thread_id=self.english_word_counter_thread.id,
                    assistant_id=self.english_word_counter_assistant.id,
                    additional_messages=[{"role": "user","content": user_response }],
                    event_handler= english_word_counter_event_handler,
            ) as stream:
                stream.until_done()
            
            response_json = json.loads(english_word_counter_event_handler.current_response)
            english_words_number = response_json.get('number_of_english_words', 0)
            print("Number of English Words:", english_words_number)
            return english_words_number
        

        english_words_number = count_english_word(user_response)
        
        
        return english_words_number / len(words)

    def calculate_misspellings_score(self, user_response):
        words = re.findall(r'\b\w+\b', user_response.lower())
        misspellings = spell.unknown(words)
        misspellings_score = max(0, 1 - len(misspellings) / len(words)) if words else 1
        return misspellings_score

    def calculate_overall_performance_score(self, user_response, expected_response):

        response_score = self.calculate_response_score()

        english_words_penalty = self.calculate_english_words_score(user_response)

        advanced_vocab_bonus = self.calculate_advanced_vocab_score(user_response, self.users_cefr_level)


        print("response score " + str(response_score))
        print("english words penalty " + str(english_words_penalty))
        print("advanced vocab bonus " + str(advanced_vocab_bonus))

        # Combine scores to get the final performance score
        final_score = response_score + advanced_vocab_bonus - english_words_penalty
        print("final score ", final_score)
        return final_score

    def calculate_updated_rating(self, user_response, expected_response, difficulty_level):
        # Example evaluation logic
        performance_score = self.calculate_overall_performance_score(user_response=user_response, expected_response=expected_response)  # Assume perfect performance for demonstration
        

        user_rating = self.users_rating
        expected_score = 1 / (1 + 10 ** ((difficulty_level - user_rating) / 400))
        
        # Elo rating adjustment
        k = 5
        new_rating = user_rating + k * (performance_score - expected_score)
        print("change in elo ", str(k * (performance_score - expected_score)))
        if new_rating < 0:
            new_rating = 0
        self.users_rating = int(new_rating)
        print(f"Updated Rating: {self.users_rating}")




chat1 = OpenAIChat(api_key=api_key)

topics_to_practice_list = [   "general conversation", "introductions",
    "weather",
    "clothing",
    "sports",
    "music",
    "animals",
    "travel",
    "food"]


@app.route('/set-up-chat', methods=['POST'])
def set_up_chat():


    # Access the JSON data sent in the POST request
    data = request.get_json()


    
    # Extract 'conversation_topic' and 'users_rating' from the JSON payload
    conversation_topic = data.get('conversation_topic')
    users_rating = data.get('users_rating', 300)  # Default to 300 if not provided
    language = data.get('language', 'Spanish')

    # Set the chat topic
    chat1.set_chat_topic(conversation_topic)
    chat1.set_language(language)
    chat1.set_users_rating(300)
    
    # Update the user's rating
    chat1.users_rating = int(users_rating)
    return 'Chat Set Up'

@app.route('/generate-response', methods=['POST'])
def generate_response():
    # Access the JSON data sent in the POST request
    data = request.get_json()
    
    # Extract 'prompt' and 'messagesList' from the JSON payload
    user_input = data.get('input')
    messagesList = data.get('messages')
    conversation_topic = data.get('conversation_topic')
    users_rating = data.get('users_rating')
    
    bots_response, users_rating = chat1.send_message(user_input)
        


    # print(response.choices[0].message.content)

  

    # response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(payload))
 
  
    # return jsonify({'data': response.choices[0].message.content.strip()})
    return jsonify({'data': bots_response, 'users_rating': users_rating})

@app.route('/reset-chat', methods=['POST'])
def reset_chat():
    chat1.reset_chat()
    return jsonify({'message': 'Chat has been reset.'}), 200

@app.route('/check-server', methods=['GET'])
def check_server():
    server_info = request.environ.get('SERVER_SOFTWARE', 'Unknown')
    return jsonify({'server': server_info}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


