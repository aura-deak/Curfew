#!/usr/bin/env python3
import datetime
from date_type import get_date_type

def is_in_restricted_hours(start_hour, start_minute, end_hour, end_minute):
    now = datetime.datetime.now().time()
    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)
    
    if start_time < end_time:
        return start_time <= now <= end_time
    else:
        return now >= start_time or now <= end_time

def is_in_restricted_hours_for_today(restricted_hours_dict):
    date_type = get_date_type()
    
    if date_type not in restricted_hours_dict:
        return False
    
    hours_list = restricted_hours_dict.get(date_type, [])
    
    for period in hours_list:
        if is_in_restricted_hours(
            period['start_hour'],
            period['start_minute'],
            period['end_hour'],
            period['end_minute']
        ):
            return True
    return False