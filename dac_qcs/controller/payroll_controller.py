# Copyright (c) 2020, Quark Cyber Systems and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import dateutil.parser
import dateutil.relativedelta

from frappe.model.document import Document
from frappe.utils import today, getdate, get_time

from datetime import timedelta, datetime
from erpnext.hr.doctype.holiday_list.holiday_list import is_holiday


def salary_slip_deduction(salary_slip, method):
    base = base_salary(salary_slip)
    salary_slip.set('gross_pay_qcs', base)
    get_leave_details(salary_slip)
    if not salary_slip.deductions:
        salary_slip.set("deductions", [])
    if not salary_slip.cancel_tardiness:
        calculate_tardiness(salary_slip)


def get_leave_details(salary_slip):
    employee = salary_slip.employee
    start_date = getdate(salary_slip.start_date)
    end_date = getdate(salary_slip.end_date)
    total_annual_leave = leave_days_count(employee, start_date, end_date, 'Annual Leave')
    salary_slip.set('total_annual_leave', total_annual_leave)
    total_sick_leave = leave_days_count(employee, start_date, end_date, 'Sick Leave')
    salary_slip.set('total_sick_leave', total_sick_leave)
    total_without_pay = leave_days_count(employee, start_date, end_date, 'Without Pay')
    salary_slip.set('total_without_pay', total_without_pay)
    total_compassionate_leave = leave_days_count(employee, start_date, end_date, 'Compassionate Leave')
    salary_slip.set('total_compassionate_leave', total_compassionate_leave)
    total_maternity_leave = leave_days_count(employee, start_date, end_date, 'Maternity Leave')
    salary_slip.set('total_maternity_leave', total_maternity_leave)
    total_education_leave = leave_days_count(employee, start_date, end_date, 'Education')
    salary_slip.set('total_education_leave', total_education_leave)


def leave_days_count(employee, start_date, end_date, leave_type='None'):
    leave_days = 0
    leave_days_list = frappe.db.get_list('Attendance', filters=[
                        ['employee', '=', employee],
                        ['docstatus', '=', 1],
                        ['status', '=', 'On Leave'],
                        ['leave_type', '=', leave_type],
                        ['attendance_date', '<=', end_date],
                        ['attendance_date', '>=', start_date]
                    ],
                    fields=['name']
                    )
    leave_days = len(leave_days_list)
    return leave_days


def calculate_tardiness(salary_slip):
    late_mins = timedelta(0, 0, 0)
    early_mins = timedelta(0, 0, 0)
    attendance_details = frappe.get_all("Attendance", filters={
                                "employee": salary_slip.employee,
                                "status": "Present"
                                },
                                fields=["name", "late_in", "early_out", "time_in", "start_time", "time_out", "end_time", "attendance_date"]
                            )
    for d in attendance_details:
        if getdate(salary_slip.start_date) <= d.attendance_date <= getdate(salary_slip.end_date):
            if d.start_time and d.time_in and d.time_in > d.start_time:
                late_mins += d.time_in - d.start_time
            if d.end_time and d.time_out and d.time_out < d.end_time:
                early_mins += d.end_time - d.time_out
    check_tardiness(salary_slip, late_mins, "Tardiness Deduction - Late In")
    total_tardiness(salary_slip, late_mins, 'late_mins')
    check_tardiness(salary_slip, early_mins, "Tardiness Deduction - Early Out")
    total_tardiness(salary_slip, early_mins, 'early_mins')
    salary_slip.calculate_net_pay()


def check_tardiness(salary_slip, tardiness, salary_component):
    tardiness_mins = tardiness.total_seconds() / 60
    if tardiness_mins > 30 and tardiness_mins < 180:
        base = base_salary(salary_slip)
        amt = half_day_deduction(base)
        add_deduction(salary_slip, amt, salary_component)
    elif tardiness_mins > 180:
        base = base_salary(salary_slip)
        amt = full_day_deduction(base)
        add_deduction(salary_slip, amt, salary_component)


def total_tardiness(salary_slip, tardiness_time, ss_field='None'):
    total_tardiness_min = tardiness_time.total_seconds() / 60
    if total_tardiness_min < 1439:
        salary_slip.set(ss_field, tardiness_time)
    elif total_tardiness_min > 1439:
        salary_slip.set(ss_field, timedelta(hours=23, minutes=59, seconds=59))


def add_deduction(salary_slip, amt, salary_component="None"):
    salary_slip.append("deductions", {
        "salary_component": salary_component,
        "amount": amt
    })


def half_day_deduction(base):
    amt = base / 60
    return amt


def full_day_deduction(base):
    amt = base / 30
    return amt


def base_salary(salary_slip):
    ssa = frappe.db.get_value("Salary Structure Assignment", filters={
                "docstatus": 1,
                "employee": salary_slip.employee
            })
    ssadoc = frappe.get_doc("Salary Structure Assignment", ssa)
    base_salary = ssadoc.base
    return base_salary
