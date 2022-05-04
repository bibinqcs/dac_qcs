// Copyright (c) 2022, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assessment Appointment Creation Tool', {
	onload(frm) {
		frm.disable_save();
		frm.set_query('appointment_type', 'sessions', () => {
			return {
				filters: {
					therapy_qcs: 0
				}
			}
		})
	},
	refresh(frm) {
		frm.add_custom_button(__('Create Appointments'), function() {
			return frm.trigger('appointment_sessions')
		});
	},
	appointment_sessions(frm) {
		for (var i=0; i < frm.doc.sessions.length; i++) {
			frappe.call({
				method: "dac_qcs.dac_module.doctype.therapy_appointment_creation_tool.therapy_appointment_creation_tool.create_patient_appointment",
				args: {
					patient: frm.doc.patient,
					practitioner: frm.doc.sessions[i].practitioner,
					appointment_type: frm.doc.sessions[i].appointment_type,
					duration: frm.doc.sessions[i].duration,
					date: frm.doc.sessions[i].date,
					time: frm.doc.sessions[i].time
				},
				callback: (r) => {
					// on success
					frappe.show_alert({
						message:__('Appointment Created ' + r.message),
						indicator:'green'
						}, 5);
				}
			});
		}
	}
});
