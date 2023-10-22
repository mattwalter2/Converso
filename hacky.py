import openai
import os
import urllib.parse
x=input("Enter Language you want to learn")
conversation_history=[]


open_ai_api_key="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"
openai.api_key=open_ai_api_key
# file= openai.File.create(
#  file=open("test.jsonl", "rb"),
#  purpose='fine-tune'
# ) 
# openai.FineTuningJob.create(training_file=file.id, model="gpt-3.5-turbo")
# #completion=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "You are a poetic assistant, skilled in explaining complex"}, {"role": "user", "content": user_text}])
while True:
  user_text=input("Type your question for the bot")
  completion = openai.ChatCompletion.create(
    model="ft:gpt-3.5-turbo-0613:personal::8CWguB4V",
    messages=[{"role": "system", "content": f"You are designed to help the user learn {x}. You converse with the user in {x} talking about food. If the user makes a mistake you correct them and continue talking in the conversation with them."}, {"role": "user", "content": user_text}]
  )
  #print(completion.choices[0].message)

  if completion is not None: 
    decoded_response = urllib.parse.unquote(completion.choices [0]. message. content)
    print (decoded_response)
    conversation_history.append(user_text)
    conversation_history.append(decoded_response)
  else: 
    print("Error creating or sending OpenAI ChatCompletion request.")





