// Copyright (c) 2022, Christopher Njogu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Consolidated Accounts Balances"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"account",
			"label": __("Group Account"),
			"fieldtype": "Link",
			"options": "Account",
			"reqd": 1,
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company')
				return {
					"query": "erpnext.controllers.queries.get_account_list",
					"filters": [
						// ['Account', 'account_type', 'in', 'Bank, Cash'],
						['Account', 'is_group', '=', 1],
						['Account', 'disabled', '=', 0],
						['Account', 'company', '=', company],
					]
				}
			}
		},
		{
			"fieldname":"as_of_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		}
	]
};
