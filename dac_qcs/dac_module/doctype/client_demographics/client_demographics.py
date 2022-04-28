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
        'communication_language_qcs': demographics_data.language
    })
    patient_data = frappe.get_doc('Patient', patient)
    frappe.db.set_value('Customer', patient_data.customer, {
        'customer_name': new_full_name
    })
    frappe.msgprint(
        msg='Client Profile Details Updated',
        title='Message'
    )


def rename_doc_link():
    frappe.rename_doc('Patient', patient, new_full_name)
    frappe.db.set_value('Client Demographics', client_demographics, 'patient', new_full_name, update_modified=False)
    frappe.rename_doc('Customer', patient_data.customer, new_full_name)
    frappe.db.set_value('Patient', new_full_name, 'customer', new_full_name, update_modified=False)
