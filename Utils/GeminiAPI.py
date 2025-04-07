import google.generativeai as genai

# Unlike OpenAI, gemini doesn't use request body, but to keep the uniform input, we will use it
default_request_body = {
    "model": "gemini-1.5-flash",
    "system_prompt": "You are a helpful assistant.",
    "temperature": 0.7,
}


class GeminiChatBot:
    def __init__(self, api_key, initial_request_body):
        if "system_prompt" not in initial_request_body:
            raise ValueError("messages not in request_body")
        if "model" not in initial_request_body:
            raise ValueError("model not in request_body")
        self.model = initial_request_body['model']
        self.system_prompt = initial_request_body['system_prompt']
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name=self.model, system_instruction=self.system_prompt)
        self.chat_history = []

        if 'temperature' in initial_request_body:
            self.generation_config = genai.types.GenerationConfig(temperature=initial_request_body['temperature'])

    # define the openai interface
    def try_query_Gemini(self, **request_body):
        model = request_body["model"]
        chat = model.start_chat(
            history=request_body['history']
        )
        prompt = request_body["prompt"]
        response = chat.send_message(prompt, generation_config=request_body["generation_config"])
        return response

    @staticmethod
    def accept_Gemini_response(response):
        res_stop = True
        # first check if the response is complete
        if not response._done:
            res_stop = False

        # Other checks in the future
        return res_stop

    def query_Gemini(self, **request_body):
        response = self.try_query_Gemini(**request_body)
        # if response failed
        timeout = 0
        while not self.accept_Gemini_response(response):
            response = self.try_query_Gemini(**request_body)
            timeout += 1
            if timeout > 10:
                raise Exception("Query failed")
        return response

    def chat(self, prompt):
        '''
        for gemini we are not puting a interactive chatbot with history, just zero shot.
        No need to add the print feature
        '''
        request_body = {
            "model": self.model,
            "generation_config": self.generation_config,
            "history" : self.chat_history,
            "prompt": prompt,
        }
        response = self.query_Gemini(**request_body)

        return response.text
    def set_chat_history(self, chat_history):
        self.chat_history = chat_history


# Unlike OpenAI, gemini doesn't use request body, but to keep the uniform input, we will use it

