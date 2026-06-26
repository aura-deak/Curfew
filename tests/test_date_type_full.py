#!/usr/bin/env python3
import pytest
from unittest.mock import patch
from date_type import get_date_type
import datetime

def test_get_date_type_weekday_monday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = True
    
    date = datetime.date(2024, 1, 15)
    assert date.weekday() == 0
    assert get_date_type(date) == 'workday'

def test_get_date_type_weekday_friday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = True
    
    date = datetime.date(2024, 1, 19)
    assert date.weekday() == 4
    assert get_date_type(date) == 'workday'

def test_get_date_type_weekend_saturday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = False
    
    with patch('date_type.get_holiday_detail') as mock_get_holiday_detail:
        mock_get_holiday_detail.return_value = (False, None)
    
    date = datetime.date(2024, 1, 20)
    assert date.weekday() == 5
    assert get_date_type(date) == 'weekend'

def test_get_date_type_weekend_sunday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = False
    
    with patch('date_type.get_holiday_detail') as mock_get_holiday_detail:
        mock_get_holiday_detail.return_value = (False, None)
    
    date = datetime.date(2024, 1, 21)
    assert date.weekday() == 6
    assert get_date_type(date) == 'weekend'

def test_get_date_type_holiday_overrides_weekend():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = False
    
    with patch('date_type.get_holiday_detail') as mock_get_holiday_detail:
        mock_get_holiday_detail.return_value = (True, '国庆节')
    
    date = datetime.date(2024, 10, 1)
    assert get_date_type(date) == 'holiday'
