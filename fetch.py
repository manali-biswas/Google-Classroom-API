import dateutil.parser
from googleapiclient.discovery import build
import datetime
from datetime import date
import requests
from google.oauth2.credentials import Credentials
from dateutil.tz import tzutc,tzlocal

class TMEntry(object):
    def __init__(self, entity_id=None, todo_id=None, calendar_event_id=None, input_source=None, entity=None,
                 duration_count=None, duration=None, frequency=None, recurring=False, all_day_event=False,
                 start_date=None, end_date=None, start_time=None, end_time=None, attendees=None, intent=None,
                 raw_text=None):
        self.entity_id = entity_id
        self.todo_id = todo_id
        self.calendar_event_id = calendar_event_id
        self.input_source = input_source   #value : voice
        self.entity = entity               #subject
        self.intent = intent               #value: task
        self.attendees = attendees        
        self.duration_count = duration_count #Event duration count. Example, for 2 Day, it will be 2
        self.duration = duration           # CalendarEntities. Example, for 2 Day, it will be Day
        self.frequency = frequency
        self.all_day_event = all_day_event
        self.recurring = recurring
        self.start_date = start_date       #task start date
        self.end_date = end_date           #task end date
        self.start_time = start_time      
        self.end_time = end_time          
        self.raw_text = raw_text

def auth(access_token):
    """Gets credentials.
    """
    
    creds = Credentials(token=access_token,client_id=None,client_secret=None,token_uri=None,refresh_token=None)
    
    return creds

#margin- Time Duration. E.g.: datetime.timedelta(days=3)
#access_token- To access the classroom

def classTasks(access_token, margin) :
    """Returns all the tasks of a student which are to be submitted within given time duration.
    """
    creds=auth(access_token)
    service = build('classroom', 'v1', credentials=creds)

    # Call the Classroom API to get all courses

    courses=[]
    page_token=None
    while True:
        response = service.courses().list(pageSize=500).execute()
        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    if not courses:
        return courses
    else:
        tasks = []
        finalTasks=[]
        today=date.today()
        for course in courses:
            work=[]
            page_token=None

            # Call the Classroom API to get all tasks for the course within the time duration

            response = service.courses().courseWork().list(pageToken=page_token, orderBy='dueDate',pageSize=500,courseId=course['id']).execute()
            while True:
                work.extend(response.get('courseWork', []))
                page_token = response.get('nextPageToken', None)
                if work:
                    ld=work[len(work)-1].get('dueDate')
                if not page_token or ld==None or datetime.date(ld['year'],ld['month'],ld['day'])<today or datetime.date(ld['year'],ld['month'],ld['day'])>=today+margin:
                    break
            if work and work[0].get('dueDate')!=None and today <= datetime.date(work[0]['dueDate']['year'],work[0]['dueDate']['month'],work[0]['dueDate']['day']) < today+margin:
                tasks.extend(work)
        if not tasks:
            return finalTasks
        else:

            # Check time duration for each task and append TMEntry objects

            for task in tasks:
                d=task.get('dueDate')
                if d!=None:
                    e=datetime.date(d['year'],d['month'],d['day'])
                    t=task.get('dueTime')
                    if today <= e < today+margin:
                        s=dateutil.parser.isoparse(task['creationTime'])
                        if(t!=None):
                            #Convert to correct timezone and check
                            final=datetime.datetime(d['year'],d['month'],d['day'],t['hours'],t['minutes'],tzinfo=tzutc())
                            final=final.astimezone(tzlocal())
                            if today<= final.date() <= today+margin:
                                s=s.replace(tzinfo=tzutc())
                                s=s.astimezone(tzlocal())
                                e=final.date()
                                # Make TMEntry objects

                                obj=TMEntry(entity=task['title'],intent='classroomTask',input_source='voice',start_date=s.date(),end_date=e,start_time=s.time(),end_time=final.time())
                                finalTasks.append(obj)
                        else:
                            obj=TMEntry(entity=task['title'],intent='classroomTask',input_source='voice',start_date=s.date(),end_date=e,start_time=s.time(),end_time=None)
                            finalTasks.append(obj)
            return finalTasks