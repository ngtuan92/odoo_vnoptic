from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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

    @api.model
    def create(self, vals):
        """Override create để phân biệt product_type"""
        product_type = vals.get('product_type', 'lens')

        # Chỉ tạo lens_ids nếu product_type là 'lens'
        if product_type != 'lens':
            # Xóa lens_ids nếu có trong vals
            if 'lens_ids' in vals:
                del vals['lens_ids']

        # Chỉ tạo opt_ids nếu product_type là 'opt'
        if product_type != 'opt':
            if 'opt_ids' in vals:
                del vals['opt_ids']

        return super().create(vals)

    def write(self, vals):
        """Override write để đảm bảo chỉ lưu đúng loại"""
        product_type = vals.get('product_type') or self.product_type

        # Nếu đang đổi product_type
        if 'product_type' in vals:
            # Xóa dữ liệu không phù hợp
            if vals['product_type'] != 'lens':
                # Xóa tất cả lens_ids
                self.lens_ids.unlink()
                if 'lens_ids' in vals:
                    del vals['lens_ids']

            if vals['product_type'] != 'opt':
                # Xóa tất cả opt_ids
                self.opt_ids.unlink()
                if 'opt_ids' in vals:
                    del vals['opt_ids']

        return super().write(vals)

    @api.model
    def default_get(self, fields_list):
        """Override default_get to prevent _unknown object errors"""
        res = super().default_get(fields_list)
        
        # Initialize all Many2one fields to False to prevent _unknown objects
        many2one_fields = [
            'supplier_id', 'group_id', 'status_group_id', 'warranty_id',
            'currency_zone_id', 'status_product_id'
        ]
        
        for field in many2one_fields:
            if field in fields_list and field not in res:
                res[field] = False
        
        return res

    def action_fix_product_type(self):
        """Fix product_type for existing products based on lens_ids/opt_ids or group_id"""
        for product in self:
            # Skip if already has correct product_type
            if product.product_type and product.product_type != 'lens':
                continue
                
            # Method 1: Auto-detect based on existing lens_ids/opt_ids
            if product.lens_ids:
                product.product_type = 'lens'
            elif product.opt_ids:
                product.product_type = 'opt'
            # Method 2: Detect based on group_id name (for API synced products)
            elif product.group_id:
                group_name = product.group_id.name
                if 'Mắt' in group_name or 'Lens' in group_name or 'lens' in group_name:
                    product.product_type = 'lens'
                elif 'Gọng' in group_name or 'Optical' in group_name or 'opt' in group_name.lower():
                    product.product_type = 'opt'
                else:
                    product.product_type = 'accessory'
            else:
                # If no detail data and no group, keep as accessory or default
                if not product.product_type:
                    product.product_type = 'accessory'
        
        return True

    @api.model
    def cron_fix_all_product_types(self):
        """Cron job to fix all product types - can be run manually"""
        products = self.search([])
        products.action_fix_product_type()
        return True
