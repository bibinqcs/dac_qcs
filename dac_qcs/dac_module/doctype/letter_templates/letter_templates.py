# Copyright (c) 2021, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _, throw
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.jinja import validate_template
from six import string_types


class LetterTemplates(Document):
	def validate(self):
		if self.letter_content:
			validate_template(self.letter_content)

@frappe.whitelist()
def get_letter_template(template_name, doc):
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	letter_template = frappe.get_doc("Letter Templates", template_name)

	if letter_template.letter_content:
		return frappe.render_template(letter_template.letter_content, doc)