import google.genai as genai

client = genai.Client(api_key="AIzaSyCP8P4Lm2SWjduioY13EPuAhuxvsPe5p1Y")

for model in client.models.list():
    print(model.name)