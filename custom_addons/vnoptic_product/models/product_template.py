from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cid = fields.Char("Product Code", required=True)
    eng_name = fields.Char("English Name")
    trade_name = fields.Char("Trade Name")

    rt_price = fields.Float("Retail Price")
    ws_price = fields.Float("Wholesale Price")
    ct_price = fields.Float("Cost Price")
    or_price = fields.Float("Original Price")
    ws_price_max = fields.Float("Wholesale Price Max")
    ws_price_min = fields.Float("Wholesale Price Min")

    access_total = fields.Integer("Accessory Total")
    cid_ncc = fields.Char("Supplier code")
    unit = fields.Char("Unit")
    uses = fields.Text("Uses")
    guide = fields.Text("Guide")
    warning = fields.Text("Warning")
    preserve = fields.Text('Preserve')
    tax_rate = fields.Float('Tax Rate')

    supplier_id = fields.Many2one('res.partner', string='Supplier')
    group_id = fields.Many2one('product.group', string='Product Group')
    status_group_id = fields.Many2one('product.status', string='Status Product Group')
    warranty_id = fields.Many2one('product.warranty', 'Warranty')
    currency_zone_id = fields.Many2one('res.currency', 'Currency Zone')
    status_product_id = fields.Many2one('product.status', 'Status Product')

    product_type = fields.Selection([
        ('lens', 'Lens'),
        ('opt', 'Optical Product'),
        ('accessory', 'Accessory')
    ], string='Product Type', default='lens')

    lens_ids = fields.One2many('product.lens', 'product_tmpl_id', 'Lens Details')
    opt_ids = fields.One2many('product.opt', 'product_tmpl_id', 'Optical Details')
