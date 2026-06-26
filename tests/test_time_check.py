#!/usr/bin/env python3
import pytest
from unittest.mock import patch
from curfew.time_check import is_in_restricted_hours, is_in_restricted_hours_for_today
import datetime

def test_is_in_restricted_hours_within_range():
    test_time = datetime.time(10, 30)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(10, 0, 11, 0) == True

def test_is_in_restricted_hours_before_range():
    test_time = datetime.time(9, 30)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(10, 0, 11, 0) == False

def test_is_in_restricted_hours_after_range():
    test_time = datetime.time(11, 30)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(10, 0, 11, 0) == False

def test_is_in_restricted_hours_cross_midnight():
    test_time = datetime.time(23, 30)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(22, 0, 2, 0) == True

    test_time = datetime.time(1, 30)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(22, 0, 2, 0) == True

    test_time = datetime.time(12, 0)
    with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
        mock_datetime_class.now.return_value.time.return_value = test_time
        assert is_in_restricted_hours(22, 0, 2, 0) == False

def test_is_in_restricted_hours_for_today_workday():
    with patch('curfew.time_check.get_date_type') as mock_get_date_type:
        mock_get_date_type.return_value = 'workday'
        
        restricted_hours = {
            'workday': [{'start_hour': 10, 'start_minute': 0, 'end_hour': 11, 'end_minute': 0}],
            'weekend': [],
            'holiday': []
        }
        
        test_time = datetime.time(10, 30)
        with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
            mock_datetime_class.now.return_value.time.return_value = test_time
            assert is_in_restricted_hours_for_today(restricted_hours) == True

        test_time = datetime.time(9, 30)
        with patch('curfew.time_check.datetime.datetime') as mock_datetime_class:
            mock_datetime_class.now.return_value.time.return_value = test_time
            assert is_in_restricted_hours_for_today(restricted_hours) == False

def test_is_in_restricted_hours_for_today_no_restrictions():
    with patch('curfew.time_check.get_date_type') as mock_get_date_type:
        mock_get_date_type.return_value = 'workday'
        
        restricted_hours = {
            'workday': [],
            'weekend': [],
            'holiday': []
        }
        
        assert is_in_restricted_hours_for_today(restricted_hours) == False

def test_is_in_restricted_hours_for_today_invalid_date_type():
    with patch('curfew.time_check.get_date_type') as mock_get_date_type:
        mock_get_date_type.return_value = 'invalid'
        
        restricted_hours = {
            'workday': [{'start_hour': 10, 'start_minute': 0, 'end_hour': 11, 'end_minute': 0}]
        }
        
        assert is_in_restricted_hours_for_today(restricted_hours) == False
