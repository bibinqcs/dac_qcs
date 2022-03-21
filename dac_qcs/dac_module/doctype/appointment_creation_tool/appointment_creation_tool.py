# Copyright (c) 2022, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AppointmentCreationTool(Document):
    pass


@frappe.whitelist()
def create_patient_appointment(patient, practitioner, appointment_type, duration, date, time):
    p_appointment = frappe.new_doc('Patient Appointment')
    p_appointment.patient = patient
    p_appointment.practitioner = practitioner
    p_appointment.appointment_type = appointment_type
    p_appointment.duration = duration
    p_appointment.appointment_date = date
    p_appointment.appointment_time = time
    p_appointment.save()
    message = p_appointment.name
    return message
