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

    group_type_id = fields.Many2one('product.group.type', string='Nhóm sản phẩm')

    # Product type - changed from computed to regular field with onchange
    product_type = fields.Selection([
        ('lens', 'Lens'),
        ('opt', 'Optical'),
        ('accessory', 'Accessory')
    ], string='Loại sản phẩm', readonly=True)

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

    # Lens fields
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

    # Opt fields
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
    material_front_ids = fields.Many2many(
        'product.material', 'wiz_material_front_rel', 'wizard_id', 'material_id', string='Chất liệu mặt trước')
    material_temple_ids = fields.Many2many(
        'product.material', 'wiz_material_temple_rel', 'wizard_id', 'material_id', string='Chất liệu càng')
    color = fields.Char('Mã màu')
    lens_color = fields.Char('Màu kính')
    temple_color = fields.Char('Màu chuôi')
    lens_width = fields.Integer('Dài mắt')
    lens_height = fields.Integer('Cao mắt')
    bridge_width = fields.Integer('Đầu cầu')
    temple_width = fields.Integer('Dài gọng')
    lens_span = fields.Integer('Ngang mắt')

    # ONCHANGE DISABLED - will be triggered manually in action_next
    # @api.onchange('group_type_id')
    def _update_product_type_from_group(self):
        """Update product_type based on group_type_id - called manually"""
        if not self.group_type_id:
            self.product_type = False
        else:
            mapping = {
                'Mắt': 'lens',
                'Gọng': 'opt',
                'Khác': 'accessory'
            }
            self.product_type = mapping.get(self.group_type_id.name, 'accessory')

            # Clear all type-specific fields to prevent _unknown object errors
            if self.product_type != 'lens':
                self.design1_id = False
                self.design2_id = False
                self.uv_id = False
                self.cl_hmc_id = False
                self.cl_pho_id = False
                self.cl_tint_id = False
                self.material_id = False
                self.coating_ids = False

            if self.product_type != 'opt':
                self.frame_id = False
                self.frame_type_id = False
                self.shape_id = False
                self.ve_id = False
                self.temple_id = False
                self.material_front_ids = False
                self.material_temple_ids = False

    def onchange(self, values, field_name, field_onchange):
        """Override onchange to catch _unknown object errors"""
        try:
            return super().onchange(values, field_name, field_onchange)
        except AttributeError as e:
            if "'_unknown' object has no attribute 'id'" in str(e):
                # Suppress _unknown object errors and return empty result
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Suppressed _unknown object error in onchange: {e}")
                print(f"SUPPRESSED _unknown ERROR: {e}")
                return {}
            else:
                raise

    def action_next(self):
        # Validate group_type_id is selected before moving from choose_type step
        if self.step == 'choose_type' and not self.group_type_id:
            raise UserError(_("Vui lòng chọn nhóm sản phẩm trước khi tiếp tục."))

        # Manually update product_type when moving from choose_type step
        if self.step == 'choose_type':
            self._update_product_type_from_group()

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

        # Ensure product_type is set based on group_type_id
        if self.group_type_id and not self.product_type:
            self._update_product_type_from_group()

        if not self.product_type:
            raise UserError(_("Chưa chọn nhóm sản phẩm."))

        vals = {
            'name': self.name,
            'eng_name': self.eng_name,
            'trade_name': self.trade_name,
            'unit': self.unit,
            'product_type': self.product_type,
            'supplier_id': self.supplier_id.id if self.supplier_id else False,
            'group_id': self.group_type_id.id if self.group_type_id else False,
            'x_country_id': self.country_id.id if self.country_id else False,
            'x_brand_id': self.brand_id.id if self.brand_id else False,
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
                'design1_id': self.design1_id.id if self.design1_id else False,
                'design2_id': self.design2_id.id if self.design2_id else False,
                'uv_id': self.uv_id.id if self.uv_id else False,
                'cl_hmc_id': self.cl_hmc_id.id if self.cl_hmc_id else False,
                'cl_pho_id': self.cl_pho_id.id if self.cl_pho_id else False,
                'cl_tint_id': self.cl_tint_id.id if self.cl_tint_id else False,
                'material_id': self.material_id.id if self.material_id else False,
                'coating_ids': [(6, 0, self.coating_ids.ids)]
            })]

        if self.product_type == 'opt':
            vals['opt_ids'] = [(0, 0, {
                'season': self.season,
                'model': self.model_name,
                'serial': self.serial,
                'sku': self.sku,
                'gender': self.gender,
                'frame_id': self.frame_id.id if self.frame_id else False,
                'frame_type_id': self.frame_type_id.id if self.frame_type_id else False,
                'shape_id': self.shape_id.id if self.shape_id else False,
                've_id': self.ve_id.id if self.ve_id else False,
                'temple_id': self.temple_id.id if self.temple_id else False,
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

    @api.model
    def default_get(self, fields_list):
        import logging
        _logger = logging.getLogger(__name__)

        print("\n" + "=" * 80)
        print(f"DEFAULT_GET CALLED with fields: {fields_list}")
        print("=" * 80)
        _logger.warning(f"DEFAULT_GET CALLED with fields: {fields_list}")

        res = super().default_get(fields_list)
        print(f"SUPER DEFAULT_GET returned: {res}")

        many2one_fields = [
            'group_type_id', 'supplier_id', 'brand_id', 'country_id', 'currency_id',
            'design1_id', 'design2_id', 'uv_id', 'cl_hmc_id', 'cl_pho_id',
            'cl_tint_id', 'material_id', 'frame_id', 'frame_type_id',
            'shape_id', 've_id', 'temple_id'
        ]

        many2many_fields = ['coating_ids', 'material_front_ids', 'material_temple_ids']

        for field in many2one_fields:
            if field in fields_list:
                if field not in res or res.get(field) is None:
                    res[field] = False
                    print(f"Set {field} = False")

        for field in many2many_fields:
            if field in fields_list:
                if field not in res or res.get(field) is None:
                    res[field] = [(6, 0, [])]
                    print(f"Set {field} = empty list")

        print(f"FINAL DEFAULT_GET result: {res}")
        print("=" * 80 + "\n")
        return res
