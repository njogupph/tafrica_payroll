# Copyright (c) 2022, Christopher Njogu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import erpnext
from erpnext.accounts.utils import get_balance_on


def execute(filters=None):
	columns = get_columns()
	data = []
	parent_account = filters.get("account")
	as_of_date = filters.get("as_of_date")
	accounts = frappe.db.get_list('Account', filters={'parent_account': parent_account}, fields=['name'])
	for account in accounts:
		data.append({
			"account": account.name,
			"balance": get_balance_on(account.name, as_of_date),
			"dr_cr": "Cr" if get_balance_on(account.name) < 0 else "Dr"
		})
	return columns, data


def get_columns():
	columns = [
		{
			'label': _('Account Name'),
			'fieldname': 'account',
			'options': 'Account',
			'width': 400
		},
		{
			'label': _('Balance'),
			'fieldname': 'balance',
			'fieldtype': 'Currency',
			'width': 260
		},
		{
			'label': _('Debit/Credit'),
			'fieldname': 'dr_cr',
			'fieldtype': 'Data',
			'width': 150
		}
	]

	return columns



