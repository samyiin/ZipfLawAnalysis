import openai
import copy
# this is an example, details on request body is on Openai's website
default_request_body = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "system", "content": "You are a helpful assistant."}],
    "temperature": 0.7,
}


class GPTChatBot:
    def __init__(self, api_key, initial_request_body):
        if "messages" not in initial_request_body:
            raise ValueError("messages not in request_body")
        if "model" not in initial_request_body:
            raise ValueError("model not in request_body")
        self.initial_request_body = copy.deepcopy(initial_request_body)
        self.api_key = api_key
        self.chat_history = self.initial_request_body["messages"]

    def chat(self, prompt):
        # query ChatGPT, but do not add the conversation to history
        temp_request_body = copy.deepcopy(self.initial_request_body)
        temp_request_body["messages"].append({"role": "user", "content": prompt})
        response = self._query_GPT(**temp_request_body)
        return response

    def set_chat_history(self, chat_history):
        self.chat_history = chat_history

    # define the openai interface
    def _try_query_GPT(self, **request_body):
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(**request_body)
        return response

    @staticmethod
    def _accept_gpt_response(response):
        res_stop = True
        # first check if the response is complete
        if not response.choices[0].finish_reason == "stop":
            res_stop = False
        # Other checks in the future
        return res_stop

    def _query_GPT(self, **request_body):
        response = self._try_query_GPT(**request_body)
        # if response failed
        timeout = 0
        while not self._accept_gpt_response(response):
            response = self._try_query_GPT(**request_body)
            timeout += 1
            if timeout > 10:
                raise Exception("Query failed")
        return response.choices[0].message.content
