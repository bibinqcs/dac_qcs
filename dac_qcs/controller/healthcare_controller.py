# Copyright (c) 2022, Quark Cyber Systems FZC and Contributors
# License: GNU General Public License v3. See license.txt


def update_status_backdated(patient_appointment, method):
    if not patient_appointment.status:
        patient_appointment.status = 'Open'
        patient_appointment.save()