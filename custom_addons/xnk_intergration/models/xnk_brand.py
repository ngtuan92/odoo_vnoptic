from odoo import models, fields, api


class XnkBrand(models.Model):
    _name = 'xnk.brand'
    _description = 'Brand (XNK)'
    _order = 'name'
    _rec_name = 'name'

    # Basic Fields
    name = fields.Char('Brand Name', required=True, index=True)
    code = fields.Char('Brand Code', index=True)
    description = fields.Text('Description')
    logo = fields.Image('Logo', max_width=512, max_height=512)
    active = fields.Boolean('Active', default=True)

    # Computed Field: Product Count
    product_count = fields.Integer(
        'Product Count',
        compute='_compute_product_count',
        store=False
    )

    # SQL Constraints
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Brand name must be unique!'),
    ]

    # Compute Methods
    @api.depends('name')  # Phụ thuộc giả, vì search_count không cache được
    def _compute_product_count(self):
        """Đếm số sản phẩm thuộc brand này"""
        for record in self:
            record.product_count = self.env['product.template'].search_count([
                ('x_brand_id', '=', record.id)
            ])

    # Display Name
    def name_get(self):
        """Custom display name: [Code] Name"""
        result = []
        for record in self:
            if record.code:
                name = f"[{record.code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_brand_id = fields.Many2one(
        'xnk.brand',
        string='Brand',
        ondelete='restrict',
        help="Product brand/manufacturer"
    )
