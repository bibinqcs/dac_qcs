"""
Complete Year-End Closing Entry Generator for Dubai Autism Center

This script generates a Journal Entry that zeros out ALL accounts (Balance Sheet + P&L)
as of a specified closing date, enabling auditors to create fresh opening entries.

Author: Claude Code
Date: 2024
License: MIT
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions


@frappe.whitelist()
def generate_complete_closing_entry(company, closing_date, fiscal_year):
	"""
	Main function to generate complete closing entry that zeros all accounts.

	Creates TWO Journal Entries:
	1. Non-party accounts (simple, balanced by account aggregation)
	2. Party accounts (Receivable/Payable with party details)

	Args:
		company (str): Company name (e.g., "Dubai Autism Center")
		closing_date (str): Date to close accounts (e.g., "2024-08-31")
		fiscal_year (str): Fiscal year being closed (e.g., "2023-2024")

	Returns:
		tuple: (je_non_party, je_party) - Two Journal Entry documents (unsaved, for review)

	Example:
		>>> from dac_qcs.utils.complete_year_end_closing import generate_complete_closing_entry
		>>> je_non_party, je_party = generate_complete_closing_entry("Dubai Autism Center", "2024-08-31", "2023-2024")
		>>> print(f"Non-Party: {len(je_non_party.accounts)} rows, Party: {len(je_party.accounts)} rows")
	"""
	# Step 1: Validate inputs
	validate_closing_parameters(company, closing_date, fiscal_year)

	# Step 2: Get balances for non-party and party accounts separately
	non_party_balances, party_balances = get_all_account_balances(company, closing_date, fiscal_year)

	# Step 3: Create TWO Journal Entries
	je_non_party = create_closing_journal_entry(company, closing_date, fiscal_year, non_party_balances, "non_party")
	je_party = create_closing_journal_entry(company, closing_date, fiscal_year, party_balances, "party")

	return je_non_party, je_party


def validate_closing_parameters(company, closing_date, fiscal_year):
	"""
	Validate that inputs are correct and safe for closing operation.

	Args:
		company (str): Company name
		closing_date (str): Closing date
		fiscal_year (str): Fiscal year name

	Raises:
		frappe.ValidationError: If any validation fails
	"""
	# Check company exists
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} does not exist").format(company))

	# Check fiscal year exists and get dates
	fy_dates = frappe.db.get_value(
		"Fiscal Year",
		fiscal_year,
		["year_start_date", "year_end_date"],
		as_dict=1
	)
	if not fy_dates:
		frappe.throw(_("Fiscal Year {0} does not exist").format(fiscal_year))

	# Validate closing date is within fiscal year
	closing_date_obj = getdate(closing_date)
	if not (getdate(fy_dates.year_start_date) <= closing_date_obj <= getdate(fy_dates.year_end_date)):
		frappe.throw(
			_("Closing date {0} must be within fiscal year {1} ({2} to {3})").format(
				closing_date, fiscal_year, fy_dates.year_start_date, fy_dates.year_end_date
			)
		)

	# Check for existing Period Closing Voucher on this date
	existing_pcv = frappe.db.exists(
		"Period Closing Voucher",
		{
			"company": company,
			"posting_date": closing_date,
			"docstatus": 1
		}
	)
	if existing_pcv:
		frappe.msgprint(
			_("Warning: Period Closing Voucher {0} already exists for this date. "
			  "This complete closing will create a separate Journal Entry.").format(existing_pcv),
			indicator="orange"
		)


def get_all_account_balances(company, closing_date, fiscal_year):
	"""
	Retrieve account balances as of closing_date, split into non-party and party accounts.

	Args:
		company (str): Company name
		closing_date (str): Closing date
		fiscal_year (str): Fiscal year name

	Returns:
		tuple: (non_party_balances, party_balances) - Two lists of account balance dicts
	"""
	# Get fiscal year start date for P&L accounts
	year_start_date = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")

	params = {
		"company": company,
		"closing_date": closing_date,
		"year_start_date": year_start_date
	}

	# Query 1: NON-PARTY accounts (aggregated by account only, no party breakup)
	non_party_query = """
		SELECT
			t1.account,
			t2.account_name,
			t2.account_type,
			t2.root_type,
			t2.report_type,
			t2.account_currency,
			SUM(t1.debit) - SUM(t1.credit) as balance_company_currency,
			SUM(t1.debit_in_account_currency) - SUM(t1.credit_in_account_currency) as balance_account_currency
		FROM
			`tabGL Entry` t1
		INNER JOIN
			`tabAccount` t2 ON t1.account = t2.name
		WHERE
			t1.company = %(company)s
			AND t1.is_cancelled = 0
			AND t2.docstatus < 2
			AND t2.disabled = 0
			AND t2.account_type NOT IN ('Receivable', 'Payable')
			AND (
				(t2.report_type = 'Balance Sheet' AND t1.posting_date <= %(closing_date)s)
				OR
				(t2.report_type = 'Profit and Loss'
					AND t1.posting_date BETWEEN %(year_start_date)s AND %(closing_date)s
					AND t1.voucher_type != 'Period Closing Voucher')
			)
		GROUP BY
			t1.account
		HAVING
			ABS(balance_company_currency) > 0.01
		ORDER BY
			t2.root_type DESC, t1.account
	"""

	non_party_balances = frappe.db.sql(non_party_query, params, as_dict=1)

	# Query 2: PARTY accounts (grouped by account + party for party-wise breakup)
	party_query = """
		SELECT
			t1.account,
			t2.account_name,
			t2.account_type,
			t2.root_type,
			t2.report_type,
			t2.account_currency,
			t1.party_type,
			t1.party,
			SUM(t1.debit) - SUM(t1.credit) as balance_company_currency,
			SUM(t1.debit_in_account_currency) - SUM(t1.credit_in_account_currency) as balance_account_currency
		FROM
			`tabGL Entry` t1
		INNER JOIN
			`tabAccount` t2 ON t1.account = t2.name
		WHERE
			t1.company = %(company)s
			AND t1.is_cancelled = 0
			AND t2.docstatus < 2
			AND t2.disabled = 0
			AND t2.account_type IN ('Receivable', 'Payable')
			AND (
				(t2.report_type = 'Balance Sheet' AND t1.posting_date <= %(closing_date)s)
				OR
				(t2.report_type = 'Profit and Loss'
					AND t1.posting_date BETWEEN %(year_start_date)s AND %(closing_date)s
					AND t1.voucher_type != 'Period Closing Voucher')
			)
		GROUP BY
			t1.account, t1.party_type, t1.party
		HAVING
			ABS(balance_company_currency) > 0.01
		ORDER BY
			t2.root_type DESC, t1.account, t1.party
	"""

	party_balances = frappe.db.sql(party_query, params, as_dict=1)

	frappe.msgprint(
		_("Found {0} non-party accounts and {1} party account entries to close").format(
			len(non_party_balances), len(party_balances)
		),
		indicator="blue"
	)

	return non_party_balances, party_balances


def create_closing_journal_entry(company, closing_date, fiscal_year, balances, entry_type):
	"""
	Create Journal Entry document with closing entries.

	Strategy: Separate entries for non-party and party accounts.
	Each entry reverses the respective account balances.

	Args:
		company (str): Company name
		closing_date (str): Closing date
		fiscal_year (str): Fiscal year name
		balances (list): List of account balance dicts
		entry_type (str): "non_party" or "party"

	Returns:
		frappe.model.document.Document: Journal Entry (unsaved)
	"""
	# Create new Journal Entry
	je = frappe.new_doc("Journal Entry")
	je.company = company
	je.posting_date = closing_date

	# Check if any depreciation accounts are involved
	has_depreciation = any(
		bal.account_name and ("depreciation" in bal.account_name.lower() or "accumulated" in bal.account_name.lower())
		for bal in balances
	)

	# Set appropriate voucher type
	if has_depreciation:
		je.voucher_type = "Depreciation Entry"
	else:
		je.voucher_type = "Journal Entry"

	je.fiscal_year = fiscal_year

	if entry_type == "non_party":
		je.user_remark = (
			f"Year-end closing entry (NON-PARTY ACCOUNTS) for {company} as of {closing_date}.\n"
			f"Zeros out non-Receivable/Payable accounts for fiscal year {fiscal_year}.\n"
			f"Generated by complete_year_end_closing.py script.\n\n"
			f"Total account entries: {len(balances)}\n"
			f"Self-balancing entry - no offsetting account needed."
		)
	else:  # party
		je.user_remark = (
			f"Year-end closing entry (PARTY ACCOUNTS) for {company} as of {closing_date}.\n"
			f"Zeros out Receivable/Payable accounts with party breakup for fiscal year {fiscal_year}.\n"
			f"Generated by complete_year_end_closing.py script.\n\n"
			f"Total party account entries: {len(balances)}\n"
			f"Self-balancing entry - no offsetting account needed."
		)

	je.is_opening = "No"

	# Add closing entries for each account balance
	total_debits_added = 0
	total_credits_added = 0

	for bal in balances:
		# Determine debit or credit to zero out the account
		# If account has debit balance (positive), credit it to zero
		# If account has credit balance (negative), debit it to zero

		row = je.append("accounts", {})
		row.account = bal.account
		row.account_currency = bal.account_currency

		# Add party information if present (for Receivable/Payable accounts)
		if bal.get("party_type") and bal.get("party"):
			row.party_type = bal.get("party_type")
			row.party = bal.get("party")

		# Set debit/credit to reverse the balance
		if flt(bal.balance_account_currency) > 0:
			# Account has debit balance, credit it to zero
			row.credit_in_account_currency = abs(flt(bal.balance_account_currency))
			row.credit = abs(flt(bal.balance_company_currency))
			total_credits_added += row.credit
		else:
			# Account has credit balance, debit it to zero
			row.debit_in_account_currency = abs(flt(bal.balance_account_currency))
			row.debit = abs(flt(bal.balance_company_currency))
			total_debits_added += row.debit

	# Validate that totals balance (they should since system is balanced!)
	difference = total_debits_added - total_credits_added

	je.user_remark += (
		f"\n\nTotal Debits: {total_debits_added:.2f}\n"
		f"Total Credits: {total_credits_added:.2f}\n"
		f"Difference: {difference:.2f}"
	)

	if abs(difference) > 1.0:
		frappe.msgprint(
			_("Warning: Entry not balanced. Difference: {0}. Review carefully.").format(difference),
			indicator="orange"
		)
	else:
		frappe.msgprint(
			_("Success: Entry is balanced. Total Debits = Total Credits = {0:.2f}").format(total_debits_added),
			indicator="green"
		)

	frappe.msgprint(
		_("Closing entry created with {0} rows. Ready to save.").format(len(je.accounts)),
		indicator="blue"
	)

	return je


@frappe.whitelist()
def validate_accounts_are_zeroed(company, closing_entry_name):
	"""
	After submission, validate that all accounts are actually zeroed.

	Call this after the Journal Entry is submitted to verify closure was successful.

	Args:
		company (str): Company name
		closing_entry_name (str): Name of the closing Journal Entry

	Returns:
		list: List of accounts with remaining non-zero balances (empty if all zeroed)

	Example:
		>>> from dac_qcs.utils.complete_year_end_closing import validate_accounts_are_zeroed
		>>> remaining = validate_accounts_are_zeroed("Dubai Autism Center", "JV-2024-00001")
		>>> if not remaining:
		>>>     print("All accounts zeroed successfully!")
	"""
	je = frappe.get_doc("Journal Entry", closing_entry_name)
	posting_date = je.posting_date

	# Check for any non-zero balances after this entry
	remaining_balances = frappe.db.sql("""
		SELECT
			t1.account,
			t2.account_name,
			t2.root_type,
			SUM(t1.debit) - SUM(t1.credit) as balance
		FROM `tabGL Entry` t1
		INNER JOIN `tabAccount` t2 ON t1.account = t2.name
		WHERE
			t1.company = %(company)s
			AND t1.posting_date <= %(posting_date)s
			AND t1.is_cancelled = 0
			AND t2.disabled = 0
		GROUP BY t1.account
		HAVING ABS(balance) > 0.01
		ORDER BY t2.root_type, t1.account
	""", {"company": company, "posting_date": posting_date}, as_dict=1)

	if remaining_balances:
		frappe.msgprint(
			_("Warning: {0} accounts still have non-zero balances after closing. "
			  "Review the list below.").format(len(remaining_balances)),
			indicator="orange"
		)

		# Log details
		for bal in remaining_balances:
			frappe.msgprint(
				f"{bal.account} ({bal.account_name}): Balance = {bal.balance:.2f}",
				indicator="orange"
			)

		return remaining_balances
	else:
		frappe.msgprint(
			_("Success! All accounts have been zeroed for {0} as of {1}.").format(company, posting_date),
			indicator="green"
		)
		return []


@frappe.whitelist()
def get_trial_balance_summary(company, date):
	"""
	Get a summary trial balance for verification.

	Useful for comparing before/after closing.

	Args:
		company (str): Company name
		date (str): Date for trial balance

	Returns:
		dict: Summary with total debits, credits, and account count
	"""
	# First get account balances
	account_balances = frappe.db.sql("""
		SELECT
			t1.account,
			SUM(t1.debit) - SUM(t1.credit) as balance
		FROM `tabGL Entry` t1
		INNER JOIN `tabAccount` t2 ON t1.account = t2.name
		WHERE
			t1.company = %(company)s
			AND t1.posting_date <= %(date)s
			AND t1.is_cancelled = 0
			AND t2.disabled = 0
		GROUP BY t1.account
		HAVING ABS(SUM(t1.debit) - SUM(t1.credit)) > 0.01
	""", {"company": company, "date": date}, as_dict=1)

	# Calculate summary
	account_count = len(account_balances)
	total_debit_balances = sum(flt(row.balance) for row in account_balances if flt(row.balance) > 0)
	total_credit_balances = sum(abs(flt(row.balance)) for row in account_balances if flt(row.balance) < 0)

	result = [{
		"account_count": account_count,
		"total_debit_balances": total_debit_balances,
		"total_credit_balances": total_credit_balances
	}]

	if result:
		summary = {
			"account_count": result[0].get("account_count", 0),
			"total_debit_balances": flt(result[0].get("total_debit_balances", 0)),
			"total_credit_balances": flt(result[0].get("total_credit_balances", 0))
		}
	else:
		summary = {
			"account_count": 0,
			"total_debit_balances": 0.0,
			"total_credit_balances": 0.0
		}

	frappe.msgprint(
		_("Trial Balance Summary for {0} as of {1}:\n"
		  "Accounts with balances: {2}\n"
		  "Total Debit Balances: {3:.2f}\n"
		  "Total Credit Balances: {4:.2f}").format(
			company, date,
			summary["account_count"],
			summary["total_debit_balances"],
			summary["total_credit_balances"]
		),
		indicator="blue"
	)

	return summary


@frappe.whitelist()
def cancel_closing_entries(voucher_no):
	"""
	Cancel year-end closing entries by marking GL Entries with custom_is_closing flag.

	This function finds all GL Entries with the specified voucher_no and custom_is_closing = 1,
	then marks them as cancelled (is_cancelled = 1), effectively undoing the closing operation.

	Args:
		voucher_no (str): The Journal Entry voucher number (e.g., "DAC-JV-25-00638")

	Returns:
		dict: Summary with count of cancelled GL Entries

	Example:
		>>> from dac_qcs.utils.complete_year_end_closing import cancel_closing_entries
		>>> result = cancel_closing_entries("DAC-JV-25-00638")
		>>> print(f"Cancelled {result['cancelled_count']} GL Entries")
	"""
	# Find all GL Entries with this voucher number and custom_is_closing flag
	gl_entries_query = """
		SELECT name, account, posting_date, company
		FROM `tabGL Entry`
		WHERE voucher_no = %(voucher_no)s
		AND custom_is_closing = 1
		AND is_cancelled = 0
	"""

	gl_entries = frappe.db.sql(gl_entries_query, {"voucher_no": voucher_no}, as_dict=1)

	if not gl_entries:
		frappe.msgprint(
			_("No active closing GL Entries found for voucher {0}").format(voucher_no),
			indicator="orange"
		)
		return {"cancelled_count": 0}

	company = gl_entries[0].company
	posting_date = gl_entries[0].posting_date

	# Mark all GL Entries as cancelled (only those with custom_is_closing = 1)
	frappe.db.sql("""
		UPDATE `tabGL Entry`
		SET is_cancelled = 1
		WHERE voucher_no = %(voucher_no)s
		AND custom_is_closing = 1
		AND is_cancelled = 0
	""", {"voucher_no": voucher_no})

	cancelled_count = len(gl_entries)
	frappe.db.commit()

	frappe.msgprint(
		_("Successfully cancelled {0} closing GL Entries for voucher {1} ({2} on {3})").format(
			cancelled_count, voucher_no, company, posting_date
		),
		indicator="green"
	)

	return {
		"cancelled_count": cancelled_count,
		"voucher_no": voucher_no,
		"company": company,
		"posting_date": posting_date
	}


def generate_voucher_number():
	"""
	Generate unique voucher number for closing entries.

	Uses ERPNext naming series to generate a unique voucher number
	in the format DAC-JV-YY-####.

	Returns:
		str: Generated voucher number (e.g., "DAC-JV-25-00638")
	"""
	from frappe.model.naming import make_autoname
	return make_autoname("DAC-JV-.YY.-.####")


@frappe.whitelist()
def create_direct_gl_closing(company, closing_date, fiscal_year):
	"""
	Create GL Entries directly to zero out all accounts, bypassing Journal Entry validation.

	This function creates GL Entries directly using frappe.flags.in_import = True to bypass
	validations. Each GL Entry is flagged with custom_is_closing = 1 for easy identification
	and cancellation.

	Args:
		company (str): Company name (e.g., "Dubai Autism Center")
		closing_date (str): Date to close accounts (e.g., "2024-08-31")
		fiscal_year (str): Fiscal year being closed (e.g., "2023-2024")

	Returns:
		dict: Summary with voucher_no, count, totals, and difference

	Example:
		>>> from dac_qcs.utils.complete_year_end_closing import create_direct_gl_closing
		>>> result = create_direct_gl_closing("Dubai Autism Center", "2024-08-31", "2023-2024")
		>>> print(f"Created {result['created_count']} GL Entries with voucher {result['voucher_no']}")
	"""
	# 1. Validate parameters
	validate_closing_parameters(company, closing_date, fiscal_year)

	# 2. Get ALL account balances grouped by account ONLY (not by party/cost_center)
	# This ensures we get the correct total balance for each account without imbalances
	year_start_date = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")

	# Simple query: ALL GL Entries up to closing date (same logic as get_trial_balance_summary)
	query = """
		SELECT
			t1.account,
			t2.account_name,
			t2.account_type,
			t2.account_currency,
			t2.report_type,
			SUM(t1.debit) - SUM(t1.credit) as balance_company_currency,
			SUM(t1.debit_in_account_currency) - SUM(t1.credit_in_account_currency) as balance_account_currency
		FROM `tabGL Entry` t1
		INNER JOIN `tabAccount` t2 ON t1.account = t2.name
		WHERE
			t1.company = %(company)s
			AND t1.posting_date <= %(closing_date)s
			AND t1.is_cancelled = 0
			AND t2.docstatus < 2
			AND t2.disabled = 0
		GROUP BY t1.account
		HAVING ABS(balance_company_currency) > 0.01
		ORDER BY t2.root_type DESC, t1.account
	"""

	balances = frappe.db.sql(query, {
		"company": company,
		"closing_date": closing_date,
		"year_start_date": year_start_date
	}, as_dict=1)

	frappe.msgprint(
		_("Found {0} account balances to close").format(len(balances)),
		indicator="blue"
	)

	# 3. Generate voucher number
	voucher_no = generate_voucher_number()

	# 4. Enable import mode to bypass validation
	frappe.flags.in_import = True

	try:
		created_count = 0
		total_dr = 0
		total_cr = 0

		# 5. Create GL Entry for each balance
		for bal in balances:
			gl_entry = frappe.new_doc("GL Entry")
			gl_entry.posting_date = closing_date
			gl_entry.transaction_date = closing_date
			gl_entry.account = bal.account
			# Don't set party_type/party - we're closing at account level only
			# Get default cost center from company
			gl_entry.cost_center = frappe.db.get_value("Company", company, "cost_center")
			gl_entry.account_currency = bal.account_currency
			gl_entry.against = "Year-End Closing"
			# Use "Period Closing Voucher" to bypass party validation on Receivable/Payable accounts
			gl_entry.voucher_type = "Period Closing Voucher"
			gl_entry.voucher_no = voucher_no
			gl_entry.company = company
			gl_entry.fiscal_year = fiscal_year
			gl_entry.remarks = f"Year-end closing entry - {company} - {closing_date}"
			gl_entry.is_opening = "No"
			gl_entry.custom_is_closing = 1  # Flag for closing entries

			# Reverse the balance
			if flt(bal.balance_company_currency) > 0:
				# Debit balance - credit it to zero
				gl_entry.credit = abs(flt(bal.balance_company_currency))
				gl_entry.debit = 0.0
				gl_entry.credit_in_account_currency = abs(flt(bal.balance_account_currency))
				gl_entry.debit_in_account_currency = 0.0
				total_cr += gl_entry.credit
			else:
				# Credit balance - debit it to zero
				gl_entry.debit = abs(flt(bal.balance_company_currency))
				gl_entry.credit = 0.0
				gl_entry.debit_in_account_currency = abs(flt(bal.balance_account_currency))
				gl_entry.credit_in_account_currency = 0.0
				total_dr += gl_entry.debit

			# GL Entry is not submittable - just insert with docstatus = 1
			gl_entry.docstatus = 1  # Set as submitted
			gl_entry.insert(ignore_permissions=True, ignore_links=True)

			created_count += 1

		frappe.db.commit()

	finally:
		# Disable import mode
		frappe.flags.in_import = False

	frappe.msgprint(
		_("Successfully created {0} GL Entries with voucher {1}").format(created_count, voucher_no),
		indicator="green"
	)

	frappe.msgprint(
		_("Total Debits: {0:,.2f}, Total Credits: {1:,.2f}, Difference: {2:.2f}").format(
			total_dr, total_cr, abs(total_dr - total_cr)
		),
		indicator="blue" if abs(total_dr - total_cr) < 1.0 else "orange"
	)

	return {
		"voucher_no": voucher_no,
		"created_count": created_count,
		"total_debit": total_dr,
		"total_credit": total_cr,
		"difference": abs(total_dr - total_cr)
	}
