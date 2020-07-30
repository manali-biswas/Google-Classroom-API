import dateutil.parser
from googleapiclient.discovery import build
import datetime
from datetime import date
import pytz
import requests
from google.oauth2.credentials import Credentials
from dateutil.tz import tzutc,tzlocal


def auth(access_token):
    """Gets credentials.
    """
    
    creds = Credentials(token=access_token,client_id=None,client_secret=None,token_uri=None,refresh_token=None)
    
    return creds


def get_task_due_date(access_token, task_name) :
    """Returns the deadline of the task with given name.
    """
    # Get credentials
    creds=auth(access_token)
    service = build('classroom', 'v1', credentials=creds)

    # Call the Classroom API
    courses=[]
    page_token=None
    while True:
        response = service.courses().list(pageToken=page_token, pageSize=500).execute()
        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    # No course enrolled
    if not courses:
        return None
        
    else:
        for course in courses:
            page_token=None
            tasks=[]
            # Fetch all the tasks for a course         
            while True:
                response = service.courses().courseWork().list(pageToken=page_token, pageSize=500, courseId=course['id']).execute()
                tasks.extend(response.get('courseWork', []))
                page_token = response.get('nextPageToken', None)
                if not page_token:
                    break

            # Check all the tasks for a course
            for task in tasks:
                if task['title'].lower() == task_name.lower():
                    d=task.get('dueDate')

                    # Due Date not mentioned
                    if d==None:
                        return d
                    # This contains the local timezone 
                    local = tzlocal()
                    t=task.get('dueTime')
                    
                    # Due Time not mentioned
                    if t==None:
                        final=date(d['year'],d['month'],d['day'],tzinfo=tzutc())
                        return final.astimezone(local)
                    
                    final=datetime.datetime(d['year'],d['month'],d['day'],t['hours'],t['minutes'],tzinfo=tzutc())
                    return final.astimezone(local)
                        
        # If no such task found                
        return None