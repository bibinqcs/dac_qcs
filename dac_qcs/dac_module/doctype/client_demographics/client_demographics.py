# Copyright (c) 2022, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate


class ClientDemographics(Document):
    def validate(self):
        if not self.student_age:
            self.student_age = getdate(today()).year - getdate(self.date_of_birth).year
        if not self.student_full_name:
            if self.student_middle_name:
                self.student_full_name = " ".join(
                    filter(None, [
                        self.student_first_name,
                        self.student_middle_name,
                        self.student_last_name
                    ])
                )
            else:
                self.student_full_name = " ".join(
                    filter(None, [
                        self.student_first_name,
                        self.student_last_name
                    ])
                )
    pass


@frappe.whitelist()
def update_patient_details(client_demographics, patient):
    demographics_data = frappe.get_doc('Client Demographics', client_demographics)
    new_full_name = demographics_data.student_full_name
    frappe.db.set_value('Patient', patient, {
        'first_name': demographics_data.student_first_name,
        'middle_name': demographics_data.student_middle_name,
        'last_name': demographics_data.student_last_name,
        'patient_name': new_full_name,
        'dob': demographics_data.date_of_birth,
        'sex': demographics_data.gender,
        'child_nationality': demographics_data.nationality,
        'guardian_full_name': demographics_data.guardian_full_name,
        'guardian_relation': demographics_data.guardian_relation,
        'email': demographics_data.guardian_email,
        'guardian_mobile_no': demographics_data.guardian_mobile_no,
        'guardian_nationality': demographics_data.guardian_nationality,
        'guardian_passport_number': demographics_data.guardian_passport_number,
        'guardian_pp_expiry': demographics_data.guardian_pp_expiry,
        'guardian_id': demographics_data.guardian_id,
        'guardian_id_expiry': demographics_data.guardian_id_expiry
    })
    patient_data = frappe.get_doc('Patient', patient)
    frappe.db.set_value('Customer', patient_data.customer, {
        'customer_name': new_full_name
    })
    update_appointment_name(patient, new_full_name)
    update_encounter_name(patient, new_full_name)
    update_invoice_name(patient, new_full_name)
    frappe.rename_doc('Patient', patient, new_full_name)
    frappe.rename_doc('Customer', patient_data.customer, new_full_name)
    frappe.msgprint(
        msg='Client Profile Details Updated',
        title='Message'
    )


def update_appointment_name(patient, new_full_name):
    patient_appointment_list = frappe.db.get_all('Patient Appointment', filters={
                                'patient': patient
                            },
                            fields=['name', 'patient', 'patient_name'])
    if len(patient_appointment_list) > 0:
        for appointment in patient_appointment_list:
            if appointment.patient_name != new_full_name:
                frappe.db.set_value('Patient Appointment', appointment.name, 'patient_name', new_full_name, update_modified=False)


def update_encounter_name(patient, new_full_name):
    patient_enounter_list = frappe.db.get_all('Patient Encounter', filters={
                                'patient': patient
                            },
                            fields=['name', 'patient', 'patient_name'])
    if len(patient_enounter_list) > 0:
        for encounter in patient_enounter_list:
            if encounter.patient_name != new_full_name:
                frappe.db.set_value('Patient Encounter', encounter.name, 'patient_name', new_full_name, update_modified=False)


def update_invoice_name(patient, new_full_name):
    sales_invoice_list = frappe.db.get_all('Sales Invoice', filters={
                                'patient': patient
                            },
                            fields=['name', 'patient', 'patient_name'])
    if len(sales_invoice_list) > 0:
        for invoice in sales_invoice_list:
            if invoice.patient_name != new_full_name:
                frappe.db.set_value('Sales Invoice', invoice.name, 'patient_name', new_full_name, update_modified=False)
