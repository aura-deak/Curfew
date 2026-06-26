#!/usr/bin/env python3
import pytest
from unittest.mock import patch
from date_type import get_date_type
import datetime

def test_get_date_type_workday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = True
        
        date = datetime.date(2024, 1, 15)
        assert get_date_type(date) == 'workday'

def test_get_date_type_weekend():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = False
    
    with patch('date_type.get_holiday_detail') as mock_get_holiday_detail:
        mock_get_holiday_detail.return_value = (False, None)
        
        date = datetime.date(2024, 1, 14)
        date = datetime.date(2024, 1, 13)
        assert get_date_type(date) == 'weekend'

def test_get_date_type_holiday():
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = False
    
    with patch('date_type.get_holiday_detail') as mock_get_holiday_detail:
        mock_get_holiday_detail.return_value = (True, '春节')
        
        date = datetime.date(2024, 2, 10)
        assert get_date_type(date) == 'holiday'

def test_get_date_type_default_now():
    with patch('date_type.datetime') as mock_datetime:
        mock_datetime.datetime.now.return_value.date.return_value = datetime.date(2024, 1, 15)
    
    with patch('date_type.is_workday') as mock_is_workday:
        mock_is_workday.return_value = True
        
        assert get_date_type() == 'workday'
