# Copyright (c) 2022, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ClientDemographics(Document):
    pass


def update_patient_details(client_demographics, patient):
    demographics_data = frappe.get_doc('Client Demographics', client_demographics)
    frappe.db.set_value('Patient', patient, {
        '': demographics_data.student_first_name,
        '': demographics_data.student_middle_name,
        '': demographics_data.student_last_name,
        '': demographics_data.date_of_birth,
        '': demographics_data.gender,
        '': demographics_data.school_and_grade,
        '': demographics_data.child_live_with,
        '': demographics_data.parent_status,
        '': demographics_data.visit_purpose,
        '': demographics_data.religion,
        '': demographics_data.nationality,
        '': demographics_data.language,
        '': demographics_data.other_lang,
        '': demographics_data.language_spoken_in_home,
        '': demographics_data.siblings_age_and_gender,
        '': demographics_data.emirate,
        '': demographics_data.parent_related,
        '': demographics_data.main_concern,
        '': demographics_data.diagnosis_report,
        '': demographics_data.guardian_full_name,
        '': demographics_data.guardian_relation,
        '': demographics_data.guardian_email,
        '': demographics_data.guardian_mobile_no,
        '': demographics_data.guardian_nationality,
        '': demographics_data.guardian_passport_number,
        '': demographics_data.guardian_pp_expiry,
        '': demographics_data.guardian_id,
        '': demographics_data.guardian_id_expiry,
        '': demographics_data.father_name,
        '': demographics_data.father_prof,
        '': demographics_data.father_nationality,
        '': demographics_data.father_mob,
        '': demographics_data.mother_name,
        '': demographics_data.mother_prof,
        '': demographics_data.mother_nationality,
        '': demographics_data.mother_mob,
        '': demographics_data.blood_grp,
        '': demographics_data.other_diseases_or_medical_conditions,
        '': demographics_data.medication,
        '': demographics_data.child_pp_att,
        '': demographics_data.child_eid_att,
        '': demographics_data.guard_pp_att,
        '': demographics_data.guard_eid_att
    })
