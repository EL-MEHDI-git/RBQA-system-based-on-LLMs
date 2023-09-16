from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA, LLMChain


from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


# function to create the chain 
def create_chain(openaikey):

    persist_directory = './vectordb'
    embedding = OpenAIEmbeddings(openai_api_key=openaikey, model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=persist_directory, 
                  embedding_function=embedding)


    # by default search_type = "similarity"
    retriever = vectordb.as_retriever(search_kwargs={'k':10})

    llm = ChatOpenAI(
        openai_api_key = openaikey,
        model_name='gpt-3.5-turbo'
        )

    # create the chain to answer questions 
    qa_chain = RetrievalQA.from_chain_type(llm=llm, 
                                    chain_type="stuff", 
                                    retriever=retriever, 
                                    return_source_documents=False)
    return qa_chain


# function to create the chain 
def chatGPT(openaikey):

    chat = ChatOpenAI(model_name='gpt-3.5-turbo',
                 openai_api_key=openaikey)
    
    template="""You are a helpful assistant for our company. 

    Take the following question: {user_input}

    Based on the the documentation available on the web, provide an informative, interesting, and concise answer suitable for someone who is new to this topic"""
    

    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template="{user_input}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    chain = LLMChain(llm=chat, prompt=chat_prompt)
    

    return chain

