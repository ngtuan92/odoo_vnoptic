from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductCreationWizard(models.TransientModel):
    _name = 'product.creation.wizard'
    _description = 'VNOPTIC Product Creation Wizard'

    step = fields.Selection([
        ('choose_type', 'Chọn loại sản phẩm'),
        ('general', 'Thông tin chung'),
        ('details', 'Thông tin chi tiết'),
        ('confirm', 'Xác nhận'),
    ], default='choose_type')

    group_type_id = fields.Many2one('product.group.type', string='Nhóm sản phẩm', required=True)
    product_type = fields.Selection([
        ('lens', 'Lens'),
        ('opt', 'Optical'),
        ('accessory', 'Accessory')
    ], readonly=True)

    # Thông tin chung
    cid = fields.Char('Kí hiệu viết tắt', required=True)
    name = fields.Char('Tên đầy đủ', required=True)
    eng_name = fields.Char('Tên Tiếng Anh')
    trade_name = fields.Char('Tên Thương mại')
    unit = fields.Char('Đơn vị', default='Chiếc')
    supplier_id = fields.Many2one('res.partner', string='Nhà cung cấp')
    brand_id = fields.Many2one('xnk.brand', string='Thương hiệu')
    country_id = fields.Many2one('res.country', string='Xuất xứ')
    description = fields.Text('Mô tả')
    uses = fields.Text('Công dụng')
    guide = fields.Text('Hướng dẫn sử dụng')
    warning = fields.Text('Cảnh báo')
    preserve = fields.Text('Bảo quản')

    rt_price = fields.Float('Giá nguyên tệ')
    currency_id = fields.Many2one('res.currency', string='Đơn vị nguyên tệ')
    warranty_supplier = fields.Text('Bảo hành hãng')
    warranty_company = fields.Text('Bảo hành công ty')
    warranty_retail = fields.Text('Bảo hành bán lẻ')

    # Lens fields (ví dụ, bổ sung theo UI ảnh 1)
    sph = fields.Char('SPH')
    cyl = fields.Char('CYL')
    base_curve = fields.Char('Base Curve')
    design1_id = fields.Many2one('product.design', string='Thiết kế 1')
    design2_id = fields.Many2one('product.design', string='Thiết kế 2')
    diameter = fields.Char('Đường kính')
    prism = fields.Char('Prism')
    len_add = fields.Char('Add')
    uv_id = fields.Many2one('product.uv', string='UV')
    cl_hmc_id = fields.Many2one('product.cl', string='HMC')
    cl_pho_id = fields.Many2one('product.cl', string='Pho Coat')
    cl_tint_id = fields.Many2one('product.cl', string='Tint Coat')
    material_id = fields.Many2one('product.material', string='Material')
    coating_ids = fields.Many2many('product.coating', string='Coating')

    # Opt fields (ảnh 2)
    season = fields.Char('Season')
    model_name = fields.Char('Model')
    serial = fields.Char('Serial')
    sku = fields.Char('SKU')
    color_code = fields.Char('Color Code')
    gender = fields.Selection([('1', 'Nam'), ('2', 'Nữ'), ('3', 'Unisex')], 'Giới tính')
    frame_id = fields.Many2one('product.frame', string='Kiểu gọng')
    frame_type_id = fields.Many2one('product.frame.type', string='Loại gọng')
    shape_id = fields.Many2one('product.shape', string='Kiểu dáng mặt kính')
    ve_id = fields.Many2one('product.ve', string='Ve kính')
    temple_id = fields.Many2one('product.temple', string='Chuôi càng')
    material_front_ids = fields.Many2many('product.material', 'wiz_material_front_rel', 'wizard_id', 'material_id',
                                          string='Chất liệu mặt trước')
    material_temple_ids = fields.Many2many('product.material', 'wiz_material_temple_rel', 'wizard_id', 'material_id',
                                           string='Chất liệu càng')
    color = fields.Char('Mã màu')
    lens_color = fields.Char('Màu kính')
    temple_color = fields.Char('Màu chuôi')
    lens_width = fields.Integer('Dài mắt')
    lens_height = fields.Integer('Cao mắt')
    bridge_width = fields.Integer('Đầu cầu')
    temple_width = fields.Integer('Dài gọng')
    lens_span = fields.Integer('Ngang mắt')

    # Accessory fields bổ sung nếu cần

    @api.onchange('group_type_id')
    def _onchange_group_type(self):
        mapping = {
            1: 'lens',
            2: 'opt',
            3: 'accessory'
        }
        self.product_type = mapping.get(self.group_type_id.id, 'accessory')

    def action_next(self):
        order = ['choose_type', 'general', 'details', 'confirm']
        idx = order.index(self.step)
        self.step = order[min(idx + 1, len(order) - 1)]
        return self._reload()

    def action_prev(self):
        order = ['choose_type', 'general', 'details', 'confirm']
        idx = order.index(self.step)
        self.step = order[max(idx - 1, 0)]
        return self._reload()

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_product(self):
        self.ensure_one()
        if not self.product_type:
            raise UserError(_("Chưa chọn nhóm sản phẩm."))

        vals = {
            'cid': self.cid,
            'name': self.name,
            'eng_name': self.eng_name,
            'trade_name': self.trade_name,
            'unit': self.unit,
            'product_type': self.product_type,
            'supplier_id': self.supplier_id.id,
            'group_id': self.group_type_id.id,
            'x_country_id': self.country_id.id,
            'x_brand_id': self.brand_id.id,
            'x_note_long': self.description,
            'x_uses': self.uses,
            'x_guide': self.guide,
            'x_warning': self.warning,
            'x_preserve': self.preserve,
            'list_price': self.rt_price,
            'categ_id': self.env.ref('product.product_category_all').id,
        }

        if self.product_type == 'lens':
            vals['lens_ids'] = [(0, 0, {
                'sph': self.sph,
                'cyl': self.cyl,
                'base': self.base_curve,
                'diameter': self.diameter,
                'prism': self.prism,
                'len_add': self.len_add,
                'design1_id': self.design1_id.id,
                'design2_id': self.design2_id.id,
                'uv_id': self.uv_id.id,
                'cl_hmc_id': self.cl_hmc_id.id,
                'cl_pho_id': self.cl_pho_id.id,
                'cl_tint_id': self.cl_tint_id.id,
                'material_id': self.material_id.id,
                'coating_ids': [(6, 0, self.coating_ids.ids)]
            })]

        if self.product_type == 'opt':
            vals['opt_ids'] = [(0, 0, {
                'season': self.season,
                'model': self.model_name,
                'serial': self.serial,
                'sku': self.sku,
                'gender': self.gender,
                'frame_id': self.frame_id.id,
                'frame_type_id': self.frame_type_id.id,
                'shape_id': self.shape_id.id,
                've_id': self.ve_id.id,
                'temple_id': self.temple_id.id,
                'materials_front_ids': [(6, 0, self.material_front_ids.ids)],
                'materials_temple_ids': [(6, 0, self.material_temple_ids.ids)],
                'color': self.color,
                'lens_width': self.lens_width,
                'lens_height': self.lens_height,
                'bridge_width': self.bridge_width,
                'temple_width': self.temple_width,
                'lens_span': self.lens_span,
            })]

        product = self.env['product.template'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': product.id,
            'target': 'current'
        }
