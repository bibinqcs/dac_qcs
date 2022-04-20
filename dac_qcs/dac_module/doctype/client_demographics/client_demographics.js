// Copyright (c) 2022, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Client Demographics', {
	update_details(frm) {
		frappe.call({
			method: "dac_qcs.dac_module.doctype.client_demographics.client_demographics.update_patient_details",
			args: {
				client_demographics: frm.doc.name,
				patient: frm.doc.patient
			},
			callback: (r) => {
				frm.refresh_field("guardians")
			},
		});
	}
});
