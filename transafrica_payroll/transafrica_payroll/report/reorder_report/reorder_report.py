# Copyright (c) 2022, Christopher Njogu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff, today, add_days


def execute(filters=None):
    if not filters:
        filters = {}
    float_precision = frappe.db.get_default("float_precision")

    condition = get_condition(filters)

    diff = (getdate(filters.get("to_date")) - getdate(filters.get("from_date"))).days + 1
    if diff <= 0:
        frappe.throw(_("'From Date' must be after 'To Date'"))

    columns = get_columns()
    items = get_item_info(filters)
    consumed_item_map = get_consumed_items(condition)
    delivered_item_map = get_delivered_items(condition)
    select_warehouse = filters.get("warehouse")

    data = []
    for item in items:
        total_outgoing = flt(consumed_item_map.get(item.name, 0)) + flt(
            delivered_item_map.get(item.name, 0)
        )
        avg_daily_outgoing = flt(total_outgoing / diff, float_precision)
        reorder_level = (avg_daily_outgoing * flt(item.lead_time_days)) + flt(item.safety_stock)
        item_price = get_price_list(item.item_code)
        item_currency = get_price_list_currency(item.item_code)
        price_list = str(item_currency) + " " + str(item_price)
        stock_balance = get_balance_qty_from_sle(item.item_code, select_warehouse)
        pending_po = pending_purchase_orders(item.item_code)
        two_months_ago = str(add_days(today(), -60))
        sales_two_months = get_last_two_months(item.item_code, two_months_ago)
        shortfall = (flt(item.reorder_level) - flt(stock_balance))
        qty_to_reorder = 0
        if shortfall > 0:
            qty_to_reorder = item.minimum_reorder_qty

        total_amt = qty_to_reorder * item_price

        data.append(
            [
                item.name,
                item.item_name,
                price_list,
                stock_balance,
                pending_po,
                stock_balance,
                sales_two_months,
                item.reorder_level,
                shortfall,
                item.minimum_reorder_qty,
                qty_to_reorder,
                (str(item_currency) + " " + str(total_amt)),
            ]
        )

    return columns, data


def get_columns():
    return [
        _("Part Number") + ":Link/Item:120",
        _("Model") + ":Data:120",
        _("Buying Price") + ":Data:120",
        _("Closing Stock") + ":Float:120",
        _("Pending Purchase Order") + ":Float:120",
        _("Total Stocks Available") + ":Float:120",
        _("Last 2 Months Sales") + ":Float:120",
        _("Reorder Level") + ":Float:120",
        _("Shortfall") + ":Float:120",
        _("Minimum Reorder Qty") + ":Float:120",
        _("Quantity to order") + ":Float:120",
        _("Order Value") + ":Data:120",
    ]


def get_item_info(filters):
    from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition

    conditions = []
    if filters.get("brand"):
        conditions.append("item.brand=%(brand)s")
    conditions.append("is_stock_item = 1")

    return frappe.db.sql(
        """select name, item_name,item_code,minimum_reorder_qty,reorder_level, description, brand, item_group,
        safety_stock, lead_time_days from `tabItem` item where {}""".format(
            " and ".join(conditions)
        ),
        filters,
        as_dict=1,
    )


def get_consumed_items(condition):
    purpose_to_exclude = [
        "Material Transfer for Manufacture",
        "Material Transfer",
        "Send to Subcontractor",
    ]

    condition += """
        and (
            purpose is NULL
            or purpose not in ({})
        )
    """.format(
        ", ".join(f"'{p}'" for p in purpose_to_exclude)
    )
    condition = condition.replace("posting_date", "sle.posting_date")

    consumed_items = frappe.db.sql(
        """
        select item_code, abs(sum(actual_qty)) as consumed_qty
        from `tabStock Ledger Entry` as sle left join `tabStock Entry` as se
            on sle.voucher_no = se.name
        where
            actual_qty < 0
            and is_cancelled = 0
            and voucher_type not in ('Delivery Note', 'Sales Invoice')
            %s
        group by item_code"""
        % condition,
        as_dict=1,
    )

    consumed_items_map = {item.item_code: item.consumed_qty for item in consumed_items}
    return consumed_items_map


def get_delivered_items(condition):
    dn_items = frappe.db.sql(
        """select dn_item.item_code, sum(dn_item.stock_qty) as dn_qty
        from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
        where dn.name = dn_item.parent and dn.docstatus = 1 %s
        group by dn_item.item_code"""
        % (condition),
        as_dict=1,
    )

    si_items = frappe.db.sql(
        """select si_item.item_code, sum(si_item.stock_qty) as si_qty
        from `tabSales Invoice` si, `tabSales Invoice Item` si_item
        where si.name = si_item.parent and si.docstatus = 1 and
        si.update_stock = 1 %s
        group by si_item.item_code"""
        % (condition),
        as_dict=1,
    )

    dn_item_map = {}
    for item in dn_items:
        dn_item_map.setdefault(item.item_code, item.dn_qty)

    for item in si_items:
        dn_item_map.setdefault(item.item_code, item.si_qty)

    return dn_item_map


def get_condition(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and posting_date between '%s' and '%s'" % (
            filters["from_date"],
            filters["to_date"],
        )
    else:
        frappe.throw(_("From and To dates required"))
    return conditions


""" 
Get the Balance of an item ina given warehouse
"""


def get_balance_qty_from_sle(item_code, warehouse):
    balance_qty = frappe.db.sql(
        """select qty_after_transaction from `tabStock Ledger Entry`
        where item_code=%s and warehouse=%s and is_cancelled=0
        order by posting_date desc, posting_time desc, creation desc
        limit 1""",
        (item_code, warehouse),
    )

    return flt(balance_qty[0][0]) if balance_qty else 0.0


"""
Get the ordered items for a certain product from a certain warehouse. The
"""


def get_ordered_qty(item_code, warehouse):
    ordered_qty = frappe.db.sql(
        """
        select sum((po_item.qty - po_item.received_qty)*po_item.conversion_factor)
        from `tabPurchase Order Item` po_item, `tabPurchase Order` po
        where po_item.item_code=%s and po_item.warehouse=%s
        and po_item.qty > po_item.received_qty and po_item.parent=po.name
        and po.status not in ('Closed', 'Delivered') and po.docstatus=1
        and po_item.delivered_by_supplier = 0""",
        (item_code, warehouse),
    )

    return flt(ordered_qty[0][0]) if ordered_qty else 0


"""
Get the price list of a particular item

"""


def get_price_list(item_code):
    p_list = frappe.db.sql(
        """  
        select price_list_rate from `tabItem Price` 
        where item_code=%s 
            and buying=1 
            limit 1
        """,
        item_code,
    )
    return flt(p_list[0][0]) if p_list else 0.0


"""
Get the price list of a particular item

"""


def get_price_list_currency(item_code):
    p_currency = frappe.db.sql(
        """  
        select currency from `tabItem Price` 
        where item_code=%s 
            and buying=1 
            limit 1
        """,
        item_code,
    )

    return p_currency[0][0] if p_currency else "KES"


"""
Get the pending purchase orders for an item

"""


def pending_purchase_orders(item_code):
    po_items = frappe.db.sql(
        """
        select (sum(po_item.stock_qty) - sum(po_item.received_qty)) as po_qty
        from `tabPurchase Order` po, `tabPurchase Order Item` po_item
        where po.name = po_item.parent and po.docstatus = 1 and
        (po.status = 'To Receive and Bill' or po.status = 'To Receive')
        and po_item.item_code = %s
        """, item_code,
    )
    return flt(po_items[0][0]) if po_items else 0.00


"""
Get the sales for the last two months 

"""


def get_last_two_months(item_code, upto_date):
    si_items = frappe.db.sql(
        """select sum(si_item.stock_qty)
        from `tabSales Invoice` si, `tabSales Invoice Item` si_item
        where si.name = si_item.parent and si.docstatus = 1 
        and (si.status not in ('Cancelled','Credit Note Issued','Return','Draft'))
        and si_item.item_code = %s
        and si.posting_date >= %s
        """,
        (item_code, upto_date),
    )
    return flt(si_items[0][0]) if si_items else 0.00
