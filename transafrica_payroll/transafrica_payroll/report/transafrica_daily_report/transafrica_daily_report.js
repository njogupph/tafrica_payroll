// Copyright (c) 2023, Christopher Njogu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["TransAfrica Daily Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"width": "100px",
			"reqd": 1
		},
		{
			"fieldname":"start_date",
			"label": __("From"),
			"fieldtype": "Date",
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname":"end_date",
			"label": __("To"),
			"fieldtype": "Date",
			"reqd": 1,
			"width": "100px"
		}
	]
};
