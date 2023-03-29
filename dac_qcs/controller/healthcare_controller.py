# Copyright (c) 2022, Quark Cyber Systems FZC and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import datetime
import frappe


@frappe.whitelist()
def get_events(start, end, filters=None):
    """Returns events for Gantt / Calendar view rendering.
    :param end: End date-time.
    :param start: Start date-time.
    :param filters: Filters (JSON).
    """
    from frappe.desk.calendar import get_event_conditions
    conditions = get_event_conditions('Patient Appointment', filters)

    data = frappe.db.sql("""
        select
        `tabPatient Appointment`.name, `tabPatient Appointment`.patient, `tabPatient Appointment`.patient_name,
        `tabPatient Appointment`.practitioner, `tabPatient Appointment`.status,
        `tabPatient Appointment`.duration,
        timestamp(`tabPatient Appointment`.appointment_date, `tabPatient Appointment`.appointment_time) as 'start',
        `tabAppointment Type`.color
        from
        `tabPatient Appointment`
        left join `tabAppointment Type` on `tabPatient Appointment`.appointment_type=`tabAppointment Type`.name
        where
        (`tabPatient Appointment`.appointment_date between %(start)s and %(end)s)
        and `tabPatient Appointment`.status != 'Cancelled' and `tabPatient Appointment`.docstatus < 2 {conditions}""".format(conditions=conditions), {
            "start": start,
            "end": end
        }, as_dict=True, update={"allDay": 0})

    for item in data:
        item.end = item.start + datetime.timedelta(minutes=item.duration)

    return data


def update_status_backdated(patient_appointment, method):
    if not patient_appointment.status:
        patient_appointment.status = 'Open'
        patient_appointment.save()
