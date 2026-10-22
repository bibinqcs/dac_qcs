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
        attendance.set('time_in', None)
        attendance.set('time_out', None)
        # The five phased-out Time fields (late_in, early_out, total_working_hours,
        # total_time, diff_working_hours) are deliberately left alone: they are hidden
        # and retained as historical data only. Clearing them with "" is what produced
        # the junk timestamps in the first place, so nothing writes them any more.
        attendance.set('late_in_duration', None)
        attendance.set('early_out_duration', None)
        attendance.set('total_working_hours_duration', None)
        attendance.set('diff_working_hours_duration', None)
        attendance.set('total_time_duration', None)


def duration_seconds(value):
    """Convert a Time value to seconds for a Duration field.

    Returns None for anything not trustworthy: blanks, and values carrying
    microseconds - the latter are the artefact of clearing a Time field with "",
    not a real measurement. Still used for Shift Type.total_time, 8 of which are
    corrupt in exactly that way.
    """
    if value in (None, ""):
        return None
    if hasattr(value, "total_seconds"):
        if value.microseconds:
            return None
        return value.total_seconds()
    try:
        parts = str(value).split(".")
        if len(parts) > 1 and int(parts[1] or 0):
            return None
        h, m, sec = (parts[0].split(":") + ["0", "0"])[:3]
        return int(h) * 3600 + int(m) * 60 + int(sec)
    except (ValueError, TypeError):
        return None



def attendance_calculate_tardiness(attendance, method=None):
    if attendance.status == 'Present' and attendance.total_working_hours_duration:
        if formatted_time(attendance.time_in) > formatted_time(attendance.start_time):
            attendance.set('late_entry', 1)
            attendance.set('late_in_duration', (
                formatted_time(attendance.time_in) - formatted_time(attendance.start_time)
            ).total_seconds())
        else:
            attendance.set('late_in_duration', None)

        if formatted_time(attendance.end_time) > formatted_time(attendance.time_out):
            attendance.set('early_exit', 1)
            attendance.set('early_out_duration', (
                formatted_time(attendance.end_time) - formatted_time(attendance.time_out)
            ).total_seconds())
        else:
            attendance.set('early_out_duration', None)

        shift_seconds = attendance.total_time_duration
        if shift_seconds and shift_seconds > attendance.total_working_hours_duration:
            attendance.set('diff_working_hours_duration',
                           shift_seconds - attendance.total_working_hours_duration)
        else:
            attendance.set('diff_working_hours_duration', None)


def attendance_calculate_total_working_hours(attendance, method=None):
    time_in = attendance.time_in
    time_out = attendance.time_out
    if time_in and time_out:
        total_hours = formatted_time(time_out) - formatted_time(time_in)
        diff_hours = total_hours.total_seconds() / 3600
        if int(diff_hours) > 0:
            attendance.set('total_working_hours_duration', total_hours.total_seconds())


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
        # duration_seconds() returns None for a Shift Type whose total_time is corrupt
        # (microseconds present), so junk is not propagated onto Attendance.
        attendance.set('total_time_duration', duration_seconds(shift_total_time))
