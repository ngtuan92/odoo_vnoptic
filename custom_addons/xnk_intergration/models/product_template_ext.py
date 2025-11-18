# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplateExtension(models.Model):
    _inherit = 'product.template'

    x_eng_name = fields.Char(
        'English Name',
        help="Product name in English"
    )

    x_trade_name = fields.Char(
        'Trade Name',
        help="Commercial trade name"
    )

    x_note_long = fields.Text(
        'Long Description',
        help="Detailed product description"
    )

    x_uses = fields.Text(
        'Product Uses',
        help="Product usage instructions"
    )

    x_guide = fields.Text(
        'Usage Guide',
        help="Step-by-step usage guide"
    )

    x_warning = fields.Text(
        'Warning',
        help="Safety warnings and precautions"
    )

    x_preserve = fields.Text(
        'Preservation Instructions',
        help="Storage and preservation guidelines"
    )

    # ==================== SUPPLIER & STATUS FIELDS ====================

    x_cid_ncc = fields.Char(
        'Supplier Code (NCC)',
        help="Supplier product code"
    )

    x_accessory_total = fields.Integer(
        'Total Accessories',
        default=0,
        help="Number of accessories included"
    )

    x_status_name = fields.Char(
        'Product Status',
        help="Current product status from API"
    )

    # ==================== PRICING FIELDS ====================

    x_tax_percent = fields.Float(
        'Tax Percentage',
        digits=(5, 2),
        help="Tax rate percentage"
    )

    x_ws_price = fields.Float(
        'Wholesale Price',
        digits='Product Price',
        help="Wholesale price"
    )

    x_ct_price = fields.Float(
        'Cost Price',
        digits='Product Price',
        help="Cost price"
    )

    x_or_price = fields.Float(
        'Original Price',
        digits='Product Price',
        help="Original price from supplier"
    )

    x_ws_price_min = fields.Float(
        'Min Wholesale Price',
        digits='Product Price',
        help="Minimum wholesale price"
    )

    x_ws_price_max = fields.Float(
        'Max Wholesale Price',
        digits='Product Price',
        help="Maximum wholesale price"
    )

    # ==================== CURRENCY FIELDS ====================

    x_currency_zone_code = fields.Char(
        'Currency Zone Code',
        help="Currency zone code from API"
    )

    x_currency_zone_value = fields.Float(
        'Currency Zone Value',
        digits=(12, 2),
        help="Currency zone exchange rate"
    )

    # ==================== CATEGORY & CLASSIFICATION ====================

    x_group_type_name = fields.Char(
        'Product Group Type',
        help="Product group type classification"
    )

    # ==================== RELATIONAL FIELDS ====================

    x_country_id = fields.Many2one(
        'res.country',
        string='Country of Origin',
        ondelete='set null',
        help="Product origin country"
    )

    x_brand_id = fields.Many2one(
        'xnk.brand',
        string='Brand',
        ondelete='restrict',
        help="Product brand/manufacturer"
    )

    x_warranty_id = fields.Many2one(
        'xnk.warranty',
        string='Warranty',
        ondelete='set null',
        help="Warranty policy for this product"
    )
