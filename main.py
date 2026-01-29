
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.agents import create_agent
from tzlocal import get_localzone


load_dotenv()


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_services():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    import streamlit as st
    

    if "calendar_service" in st.session_state:
        return st.session_state.calendar_service

    creds = None

    if "GOOGLE_TOKEN_JSON" in os.environ:
        creds = Credentials.from_authorized_user_info(
            json.loads(os.environ["GOOGLE_TOKEN_JSON"]), SCOPES
        )

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            json.loads(os.environ["GOOGLE_OAUTH_JSON"]), SCOPES
        )
        creds = flow.run_console()

        # Save token into env-style format (for next deploy)
        # print("SAVE THIS TOKEN IN RENDER ENV VAR:")
        # print(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    st.session_state.calendar_service = service
    return service
#   creds = None
#   # The file token.json stores the user's access and refresh tokens, and is
#   # created automatically when the authorization flow completes for the first
#   # time.
#   if os.path.exists("token.json"):
#     creds = flow.run_local_server(
#     port=0,
#     prompt="consent",
#     access_type="offline",
#     include_granted_scopes="false",
# )

#   # If there are no (valid) credentials available, let the user log in.
#   if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#       creds.refresh(Request())
#     else:
#       flow = InstalledAppFlow.from_client_secrets_file(
#           "credentials.json", SCOPES
#       )
#       creds = flow.run_local_server(port=0)
#     # Save the credentials for the next run
#     with open("token.json", "w") as token:
#       token.write(creds.to_json())
#   return build("calendar", "v3", credentials=creds)



def get_user_timezone() -> str:
    """
    Detect the user's local time zone. Falls back to 'Asia/Kolkata' if detection fails.
    """
    try:
        return str(get_localzone())
    except Exception as e:
        print(f"Warning: Could not detect local time zone ({str(e)}). Falling back to 'Asia/Kolkata'.")
        return "Asia/Kolkata"
@tool
def create_calender_event(summary: str,start_datetime: str,end_datetime: str,location: str = "",):
  '''
  "Creates a Calander event.
  Docstring for create_calender_event
  
  :param summary: Description
  :type summary: str
  :param start_datetime: Description
  :type start_datetime: str
  :param end_datetime: Description
  :type end_datetime: str
  :param location: Description
  :type location: str
  '''
  user_timezone = get_user_timezone()
  service = get_services()
  event = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": user_timezone},
        "end": {"dateTime": end_datetime, "timeZone": user_timezone},
    }
  try:
      created = service.events().insert(calendarId="primary", body=event).execute()
      return f"Event created: {created.get('htmlLink')}"
  except HttpError as error:
        raise ValueError(f"Failed to create event: {str(error)}")

# def delete_event(event_id: str, calendar_id: str = "primary", send_updates: str = "none") -> str:
#     service = get_services()
#     try:
#         service.events().delete(
#             calendarId=calendar_id,
#             eventId=event_id,
#             sendUpdates=send_updates
#         ).execute()
#         return "Event deleted successfully."
#     except HttpError as error:
#         raise ValueError(f"Failed to delete event: {str(error)}")

model = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant")

SYSTEM_PROMPT='''
        You are a helpful and precise calendar assistant that operates in the user's local time zone (e.g., IST for Asia/Kolkata).

Event Creation Instructions:
When the user wants to create an event:
- Collect essential details: title, start time, end time/duration.
- Always create Google Calendar events using RFC3339 format.
- If the user says "today" or "tomorrow", resolve the correct date.
- Call `create_calender_event` 
- Respond with confirmation, title/time in local TZ, and link. 

'''

agent = create_agent(
    model=model,
    name="google_calendar_agent",
    tools=[create_calender_event],
    system_prompt=SYSTEM_PROMPT
)

def agent_response(user_message:str)->str:
    response=agent.invoke({"messages":[( "user",user_message)]})
    for msg in reversed(response["messages"]):
        if msg.type == "tool":
            return msg.content
    
    return response["messages"][-1].content

