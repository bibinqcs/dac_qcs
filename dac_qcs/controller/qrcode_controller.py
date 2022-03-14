# Copyright (c) 2022, Quark Cyber Systems FZC and Contributors
# License: GNU General Public License v3. See license.txt


import io
import frappe
from pyqrcode import create


def create_qrcode_image(doc, method=None):
    qrcode = doc.get("qr_code_image_qcs")
    if qrcode and frappe.db.exists({"doctype": "File", "file_url": qrcode}):
        return

    doc_name = doc.name
    doc_name_no_spaces = doc_name.replace(" ", "")
    fn_hash = frappe.generate_hash(doc_name, 2)
    filename = "QRCode-" + doc_name_no_spaces + "-" + fn_hash + ".svg"
    qr_image = io.BytesIO()
    code = create(doc_name, error='L')
    code.svg(qr_image, scale=7, quiet_zone=1)

    # File Creation
    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "is_private": 0,
        "content": qr_image.getvalue(),
        "attached_to_doctype": doc.get("doctype"),
        "attached_to_name": doc.get("name"),
        "attached_to_field": "qr_code_image_qcs"
    })

    _file.save()

    # assigning to document
    doc.db_set('qr_code_image_qcs', _file.file_url)
    doc.notify_update()


def delete_qrcode_image(doc, method=None):
    if hasattr(doc, 'qr_code_image_qcs'):
        if doc.get('qr_code_image_qcs'):
            file_doc = frappe.get_list('File', {
                'file_url': doc.get('qr_code_image_qcs')
            })
            if len(file_doc):
                frappe.delete_doc('File', file_doc[0].name)
