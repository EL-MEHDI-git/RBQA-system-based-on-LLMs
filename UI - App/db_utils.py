from sqlalchemy import create_engine, Column, BigInteger, String, JSON, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import requests

import logging
import urllib
import os
from dotenv import load_dotenv
load_dotenv()

# load environment variables
database_host = os.getenv('DATABASE_HOST')
database_port = os.getenv('DATABASE_PORT')
database_username = os.getenv('DATABASE_USERNAME')
database_password = os.getenv('DATABASE_PASSWORD')
database_db_name = os.getenv('DATABASE_DB_NAME')
database_schema_name = os.getenv('DATABASE_SCHEMA_NAME')
database_url = f'postgresql://{urllib.parse.quote_plus(database_username)}:{urllib.parse.quote_plus(database_password)}@{database_host}:{database_port}/{database_db_name}'

Base = declarative_base()

class ChatbotQuestionAnswerData(Base):
    __tablename__ = 'chatbot-qa'
    __table_args__ = {'schema': database_schema_name}
    
    id = Column(BigInteger, primary_key=True)
    timestamp = Column(DateTime)
    model = Column(String)
    question = Column(String)
    answer = Column(String)

class ChatbotFeedbackData(Base):
    __tablename__ = 'chatbot-feedback'
    __table_args__ = {'schema': database_schema_name}
    
    id = Column(BigInteger, primary_key=True)
    timestamp = Column(DateTime)
    model = Column(String)
    question = Column(String)
    answer = Column(String)
    is_useful = Column(Boolean)
    comment = Column(String)
    raw_payload = Column(JSON)

def create_connection():
    """Create a connection to the PostgreSQL database"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def insert_question_answer_data(session, timestamp, model, question, answer):
    """Insert data into the chatbot_data table"""
    chatbot_data = ChatbotQuestionAnswerData(timestamp=timestamp, model=model, question=question, answer=answer)
    session.add(chatbot_data)
    session.commit()
    #print("Q&A data inserted successfully")

def insert_feedback_data(session, timestamp, model, question, answer, is_useful, comment, raw_payload):
    """Insert data into the chatbot_data table"""
    chatbot_data = ChatbotFeedbackData(timestamp=timestamp, model=model, question=question, answer=answer, is_useful=is_useful, comment=comment, raw_payload=raw_payload)
    session.add(chatbot_data)
    session.commit()
    #print("Feedback data inserted successfully")


def send_payload_to_slack(slack_webhook_url, slack_payload):
    print(slack_payload)
    response = requests.post(slack_webhook_url, json=slack_payload)

    # # Check the response status code
    if response.status_code == 200:
        print('POST request sent successfully')
    else:
        print(f'Failed to send POST request. Status code: {response.status_code}')


db_session = create_connection()
logging.info("new db_session")