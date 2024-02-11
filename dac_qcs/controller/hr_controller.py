# Copyright (c) 2024, Quark Cyber Systems and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import dateutil.parser
import dateutil.relativedelta
import calendar

from frappe.model.document import Document
from frappe.utils import today, getdate, get_time

from datetime import timedelta, datetime
from erpnext.hr.doctype.holiday_list.holiday_list import is_holiday

from dac_qcs.utils.common import formatted_time


def attendance_custom_validate(attendance, method=None):
    attendance_set_shift_time(attendance)
    attendance_set_attendance_request_details(attendance)
    attendance_calculate_total_working_hours(attendance)
    attendance_calculate_tardiness(attendance)


def attendance_custom_before_save(attendance, method=None):
    attendance_clear_time_fields(attendance)


def attendance_clear_time_fields(attendance):
    if not attendance.status == 'Present' or attendance.attendance_request:
        attendance.set('time_in', "")
        attendance.set('time_out', "")
        attendance.set('late_in', "")
        attendance.set('early_out', "")
        attendance.set('total_working_hours', "")
        attendance.set('diff_working_hours', "")


def attendance_calculate_tardiness(attendance, method=None):
    if attendance.status == 'Present' and attendance.total_working_hours:
        if formatted_time(attendance.time_in) > formatted_time(attendance.start_time):
            attendance.set('late_entry', 1)
            attendance.late_in = formatted_time(attendance.time_in) - formatted_time(attendance.start_time)
        else:
            attendance.set('late_in', "")
        if formatted_time(attendance.end_time) > formatted_time(attendance.time_out):
            attendance.set('early_exit', 1)
            attendance.early_out = formatted_time(attendance.end_time) - formatted_time(attendance.time_out)
        else:
            attendance.set('early_out', "")
        if formatted_time(attendance.total_time) > formatted_time(attendance.total_working_hours):
            attendance.diff_working_hours = formatted_time(attendance.total_time) - formatted_time(attendance.total_working_hours)
        else:
            attendance.set('diff_working_hours', "")


def attendance_calculate_total_working_hours(attendance, method=None):
    time_in = attendance.time_in
    time_out = attendance.time_out
    if time_in and time_out:
        total_hours = formatted_time(time_out) - formatted_time(time_in)
        diff_hours = total_hours.total_seconds() / 3600
        if int(diff_hours) > 0:
            attendance.total_working_hours = total_hours


def attendance_set_attendance_request_details(attendance):
    attendance_request = attendance.attendance_request
    if attendance_request:
        attendance.time_in = frappe.db.get_value('Attendance Request', attendance_request, 'time_in')
        attendance.time_out = frappe.db.get_value('Attendance Request', attendance_request, 'time_out')


def attendance_set_shift_time(attendance):
    shift = attendance.shift

    if shift:
        attendance_date = getdate(attendance.attendance_date)
        attendance_day = calendar.day_name[attendance_date.weekday()]

        enable_friday_shift = frappe.db.get_value('Shift Type', shift, 'enable_friday_shift')
        if enable_friday_shift:
            if attendance_day == 'Friday':
                shift_start_time = frappe.db.get_value('Shift Type', shift, 'friday_start_time')
                shift_end_time = frappe.db.get_value('Shift Type', shift, 'friday_end_time')
                shift_total_time = frappe.db.get_value('Shift Type', shift, 'friday_total_time')
            else:
                shift_start_time = frappe.db.get_value('Shift Type', shift, 'start_time')
                shift_end_time = frappe.db.get_value('Shift Type', shift, 'end_time')
                shift_total_time = frappe.db.get_value('Shift Type', shift, 'total_time')
        else:
            shift_start_time = frappe.db.get_value('Shift Type', shift, 'start_time')
            shift_end_time = frappe.db.get_value('Shift Type', shift, 'end_time')
            shift_total_time = frappe.db.get_value('Shift Type', shift, 'total_time')

        attendance.start_time = shift_start_time
        attendance.end_time = shift_end_time
        attendance.total_time = shift_total_time
