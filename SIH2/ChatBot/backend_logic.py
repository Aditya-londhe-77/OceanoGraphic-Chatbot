import os
import json
from groq import Groq
import chromadb
import pandas as pd
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

DB_CONNECTION_STRING = "postgresql://postgres.nshbsuintqovdbqpcnyc:Aditya.in.77@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_HISTORY_FILE = "chat_history.json"
CHROMA_DB_PATH = "argo_vectordb"
COLLECTION_NAME = "argo_tables_schema"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY not found. Please ensure it is set in your .env file.")

try:
    engine = create_engine(DB_CONNECTION_STRING, pool_pre_ping=True)
except Exception as e:
    print(f"Failed to create database engine. Error: {e}")
    exit()

groq_client = Groq(api_key=GROQ_API_KEY)
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(name=COLLECTION_NAME)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)


# def save_chat_to_json(user_message: str, ai_response: str):
#     """Saves a user-AI interaction to a JSON file."""
#     new_entry = {
#         "timestamp": datetime.now().isoformat(),
#         "user_message": user_message,
#         "ai_response": ai_response
#     }

#     try:
#         with open(CHAT_HISTORY_FILE, 'r') as f:
#             history = json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         history = []

#     history.append(new_entry)

#     try:
#         with open(CHAT_HISTORY_FILE, 'w') as f:
#             json.dump(history, f, indent=4)
#     except Exception as e:
#         print(f"Error saving chat history to {CHAT_HISTORY_FILE}: {e}")


def is_query_data_related(user_query: str) -> bool:
    """Uses an LLM to classify if the user's query is related to the database."""
    prompt = f"""
    You are an intent classification assistant for a database chatbot.
    The database contains oceanographic data about Argo floats.
    Determine if the user's query can be answered by this database.
    - If the query is about ocean data, measurements, locations, etc., respond with ONLY "yes".
    - If it's a greeting or unrelated, respond with ONLY "no".
    User Query: "{user_query}"
    Your response (yes/no):
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.0,
        )
        response = chat_completion.choices[0].message.content.strip().lower()
        print(f"Intent check for '{user_query}': classification is '{response}'")
        return response == "yes"
    except Exception as e:
        print(f"Error during intent classification: {e}")
        return False


def get_sql_from_natural_language(user_query, selected_float=None):
    """Generates and executes a SQL query from natural language."""
    print(f"\nQuery: '{user_query}' for float: '{selected_float}'")
    query_embedding = embedding_model.encode([user_query]).tolist()

    if selected_float:
        where_filter = {"float_name": selected_float}
        print(f"Applying ChromaDB where filter: {where_filter}")
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=2,
            where=where_filter
        )
        
        if not results.get('documents') or not results['documents'][0]:
            print(f"No context found for float: {selected_float}. Aborting.")
            error_df = pd.DataFrame({"Error": [f"No specific context found for the selected float: {selected_float}"]})
            return error_df, "N/A"

    else:
        print("No float selected, performing general search.")
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=2
        )

    retrieved_context = "\n\n".join(results["documents"][0])
    db_schema = """
    Table "argo_trajectory": Columns -> "N_MEASUREMENT", "LATITUDE", "LONGITUDE".
    Table "argo_profiles": Columns -> "N_MEASUREMENT", "PRES", "TEMP", "PSAL".
    Table "argo_technical": Columns -> "TECHNICAL_PARAMETER_NAME", "TECHNICAL_PARAMETER_VALUE", "CYCLE_NUMBER".
    Table "argo_metadata": Columns -> "PLATFORM_NUMBER", "PROJECT_NAME", "PI_NAME", "LAUNCH_DATE", "FLOAT_SERIAL_NO", "SENSOR_MODEL", "FIRMWARE_VERSION".
    """
    prompt_template = f"""
    You are an expert PostgreSQL assistant. Your task is to generate a SQL query based on the user's question and the provided database context.
    You must only output the SQL query and nothing else.
    When the user says this float which means kokan coast float.
    IMPORTANT: Always enclose table and column names in double quotes (e.g., SELECT "my_column" FROM "my_table").

    Here is the database schema:
    {db_schema}

    Here is some context about the tables which might be relevant:
    {retrieved_context}

    User's Question:
    "{user_query}"

    SQL Query:
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_template}],
            model="llama-3.1-8b-instant",
            temperature=0.0,
        )
        raw_response = chat_completion.choices[0].message.content.strip()
        select_pos = raw_response.upper().find("SELECT")
        generated_sql = raw_response[select_pos:] if select_pos != -1 else raw_response
        semicolon_pos = generated_sql.find(";")
        if semicolon_pos != -1:
            generated_sql = generated_sql[:semicolon_pos + 1]
        print(f"SQL: {generated_sql}")
    except Exception as e:
        print(f"Error with Groq API: {e}")
        return pd.DataFrame({"Error": [f"Failed to generate SQL: {e}"]}), "N/A"
    try:
        with engine.connect() as connection:
            result_df = pd.read_sql_query(text(generated_sql), connection)
        return result_df, generated_sql
    except Exception as e:
        print(f"SQL execution error: {e}")
        return pd.DataFrame({"Error": [str(e)]}), generated_sql


def humanize_result(user_query, df):
    """Creates a natural language summary of the query result."""
    df_preview = df.head(50).to_string(index=False)
    
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            chat_history = json.load(f)

        chat_history_str = "\n".join([
            f"User: {entry['user_message']}\nAssistant: {entry['ai_response']}"
            for entry in chat_history
        ])
    except (FileNotFoundError, json.JSONDecodeError):
        chat_history_str = ""

    prompt = f"""
    You are an expert data analyst who writes natural language summaries of data tables.

    Here is the conversation history so far:
    {chat_history_str}

    The user just asked: "{user_query}"

    The data table below contains the complete answer:
    Data:
    {df_preview}

    Your task is to write a single, helpful sentence that directly answers the user's question based on the data.

    # --- EXAMPLES ---
    # User Question: "give me the highest 5 temperature reading of this float"
    # Good Summary: "The top 5 temperature readings range from 30.297 to 29.833."

    # User Question: "what is the lowest pressure?"
    # Good Summary: "The lowest pressure reading is 8.0 decibars."

    # User Question: "show me some salinity and temperature values"
    # Good Summary: "Here are some recent salinity and temperature readings from the float."
    # --- END EXAMPLES ---

    Based on the conversation history, the user's latest question, and the data provided, what is the best one-sentence summary?

    Summary:
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during humanization: {e}")
        return f"Here is the data I found."


def process_user_query(user_message: str, selected_float: str = None) -> str:
    """Main function to handle a user's query from start to finish."""
    
    final_response = ""
    
    if not is_query_data_related(user_message):
        final_response = ("Hello there! I'm your guide to the world's oceans. You can ask me about "
                          "water temperatures, salinity levels, or the locations of our amazing research floats. "
                          "What would you like to discover today?")
        return final_response
    try:
        df, generated_sql = get_sql_from_natural_language(user_message, selected_float=selected_float)
        
        if "Error" in df.columns:
            error_message = df['Error'].iloc[0]
            if "No specific context found" in error_message:
                final_response = f"I'm sorry, but I don't have any specific data for '{selected_float}'. Please select a float I have information about, like the Konkan Coast Float."
                return final_response
            
            print(f"SQL Error for query '{user_message}': {error_message}")
            final_response = ("I seem to have hit a snag while searching the ocean depths for that. "
                                "Could you try asking your question in a different way?")
            return final_response

        if df is None or df.empty:
            final_response = ("I searched far and wide in our ocean data but couldn't find anything matching your request. "
                                "Perhaps you could try asking about a broader topic?")
            return final_response

        explanation = humanize_result(user_message, df)
        df_preview_md = df.head(10).to_markdown(index=False)
        html_formatted_table = f"<pre>{df_preview_md}</pre>"

        final_response = (
            f"{explanation}\n\n"
            f"Data I found:\n"
            f"{html_formatted_table}"
        )
        
        # save_chat_to_json(user_message, final_response)
        
        return final_response
        
    except Exception as e:
        print(f"An unexpected error occurred in process_user_query: {e}")
        final_response = "Oops! My navigation systems seem to be down. Please try asking again in a few moments."
        return final_response