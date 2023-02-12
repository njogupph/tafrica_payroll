# Copyright (c) 2023, Christopher Njogu and contributors
# For license information, please see license.txt

from calendar import monthrange

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr, getdate
from datetime import date, timedelta, datetime


def execute(filters=None):
    end_date = datetime.strptime(filters.get("end_date"), '%Y-%m-%d')
    start_date = datetime.strptime(filters.get("start_date"), '%Y-%m-%d')
    date_range = (end_date - start_date).days + 1
    columns = []
    columns = ["Cost Center"] + ["Narration"] + ["Cumulative"] + [
        str((start_date + timedelta(days=dt)).strftime('%Y-%m-%d')) for dt in
        range(date_range)]
    data = []
    data_by_date = {}
    for i in range(date_range):
        dt = start_date + timedelta(days=i)
        posting_date_str = dt.strftime('%Y-%m-%d')
        filters["posting_date"] = posting_date_str
        sql = """
            SELECT
                cc.parent_cost_center as "Cost Center",
                SUM(total) as "Net Amount",
                SUM(total_taxes_and_charges) as "Tax",
                SUM(grand_total) as "Total Amount"
            FROM
                `tabSales Invoice` si
                JOIN `tabCost Center` cc ON cc.name = si.cost_center
            WHERE
                posting_date = %(posting_date)s
                and si.company = %(company)s
                and cc.company = %(company)s
            GROUP BY
                cc.parent_cost_center
        """

        data = frappe.db.sql(sql, filters, as_dict=True)
        for row in data:
            cost_center = row.get("Cost Center")
            if cost_center not in data_by_date:
                data_by_date[cost_center] = {}
            data_by_date[cost_center][posting_date_str] = {
                "Net Amount": row.get("Net Amount"),
                "Tax": row.get("Tax"),
                "Total Amount": row.get("Total Amount"),
            }

    grand_total_net = 0
    grand_total_tax = 0
    grand_total_amount = 0
    for cost_center in data_by_date:
        for posting_date in columns[2:]:
            grand_total_net += data_by_date[cost_center].get(posting_date, {}).get("Net Amount", 0)
            grand_total_tax += data_by_date[cost_center].get(posting_date, {}).get("Tax", 0)
            grand_total_amount += data_by_date[cost_center].get(posting_date, {}).get("Total Amount", 0)

    grand_total_row = ["Grand Total", "", grand_total_net, grand_total_tax, grand_total_amount]
    rows = [{"cost_center": "SALES"}]
    for cost_center in data_by_date:
        net_amount = [
            data_by_date[cost_center].get(posting_date, {}).get("Net Amount")
            for posting_date in columns[2:]
        ]
        tax_amount = [data_by_date[cost_center].get(posting_date, {}).get("Tax")
                      for posting_date in columns[2:]
                      ]
        total_amount = [data_by_date[cost_center].get(posting_date, {}).get("Total Amount")
                        for posting_date in columns[2:]
                        ]

        net_amount_row = [cost_center, "Net Amount"] + net_amount
        tax_amount_row = ["", "Tax"] + tax_amount
        total_amount_row = ["", "Total Amount"] + total_amount

        rows.append(net_amount_row)
        rows.append(tax_amount_row)
        rows.append(total_amount_row)

        grand_total_net = sum([value for value in net_amount_row[2:] if value is not None])
        grand_total_tax = sum([value for value in tax_amount_row[2:] if value is not None])
        grand_total_amount = sum([value for value in grand_total_row[2:] if value is not None])

        new_cols, new_rows = get_p_invoices(filters)
        # columns.append(new_cols)
        rows.extend(new_rows)

        return columns, rows


def get_p_invoices(filters=None):
    end_date = datetime.strptime(filters.get("end_date"), '%Y-%m-%d')
    start_date = datetime.strptime(filters.get("start_date"), '%Y-%m-%d')
    date_range = (end_date - start_date).days + 1
    columns = []
    columns = ["Cost Center"] + ["Narration"] + ["Cumulative"] + [
        str((start_date + timedelta(days=dt)).strftime('%Y-%m-%d')) for dt in
        range(date_range)]
    data = []
    data_by_date = {}
    for i in range(date_range):
        dt = start_date + timedelta(days=i)
        posting_date_str = dt.strftime('%Y-%m-%d')
        filters["posting_date"] = posting_date_str
        sql = """
            SELECT
                cc.parent_cost_center as "Cost Center",
                SUM(total) as "Net Amount",
                SUM(total_taxes_and_charges) as "Tax",
                SUM(grand_total) as "Total Amount"
            FROM
                `tabPurchase Invoice` si
                JOIN `tabCost Center` cc ON cc.name = si.cost_center
            WHERE
                posting_date = %(posting_date)s
                and si.company = %(company)s
                and cc.company = %(company)s
            GROUP BY
                cc.parent_cost_center
        """

        data = frappe.db.sql(sql, filters, as_dict=True)
        for row in data:
            cost_center = row.get("Cost Center")
            if cost_center not in data_by_date:
                data_by_date[cost_center] = {}
            data_by_date[cost_center][posting_date_str] = {
                "Net Amount": row.get("Net Amount"),
                "Tax": row.get("Tax"),
                "Total Amount": row.get("Total Amount"),
            }

    grand_total_net = 0
    grand_total_tax = 0
    grand_total_amount = 0
    for cost_center in data_by_date:
        for posting_date in columns[2:]:
            grand_total_net += data_by_date[cost_center].get(posting_date, {}).get("Net Amount", 0)
            grand_total_tax += data_by_date[cost_center].get(posting_date, {}).get("Tax", 0)
            grand_total_amount += data_by_date[cost_center].get(posting_date, {}).get("Total Amount", 0)

    grand_total_row = ["Grand Total", "", grand_total_net, grand_total_tax, grand_total_amount]
    rows = [{"cost_center": "PURCHASES"}]
    for cost_center in data_by_date:
        net_amount = [
            data_by_date[cost_center].get(posting_date, {}).get("Net Amount")
            for posting_date in columns[2:]
        ]
        tax_amount = [data_by_date[cost_center].get(posting_date, {}).get("Tax")
                      for posting_date in columns[2:]
                      ]
        total_amount = [data_by_date[cost_center].get(posting_date, {}).get("Total Amount")
                        for posting_date in columns[2:]
                        ]

        net_amount_row = [cost_center, "Net Amount"] + net_amount
        tax_amount_row = ["", "Tax"] + tax_amount
        total_amount_row = ["", "Total Amount"] + total_amount

        rows.append(net_amount_row)
        rows.append(tax_amount_row)
        rows.append(total_amount_row)

        grand_total_net = sum([value for value in net_amount_row[2:] if value is not None])
        grand_total_tax = sum([value for value in tax_amount_row[2:] if value is not None])
        grand_total_amount = sum([value for value in grand_total_row[2:] if value is not None])

    return columns, rows


def get_columns():
    columns = [
        {
            "fieldname": "posting_date",
            "label": "Posting Date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "Cost Center",
            "label": "Cost Center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 150
        },
        {
            "fieldname": "Net Amount",
            "label": "Net Amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "Tax",
            "label": "Tax",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "Total Amount",
            "label": "Total Amount",
            "fieldtype": "Currency",
            "width": 120
        }
    ]
    return columns
