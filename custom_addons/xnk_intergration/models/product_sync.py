# -*- coding: utf-8 -*-
import base64
import logging
import os
from io import BytesIO

import requests
import urllib3

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.fields import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class ProductSync(models.Model):
    _name = 'product.sync'
    _description = 'Product Synchronization'

    name = fields.Char('Sync Name', required=True, default='Product Sync')

    # Spring Boot credentials
    spring_boot_username = fields.Char('Enter VNOPTIC Username', required=True)
    spring_boot_password = fields.Char('Enter VNOPTIC Password', required=True)

    last_sync_date = fields.Datetime('Last Sync Date')
    sync_status = fields.Selection([
        ('never', 'Never Synced'),
        ('success', 'Success'),
        ('error', 'Error')
    ], default='never', string='Status')
    sync_log = fields.Text('Sync Log')

    # Thống kê sau khi sync
    total_synced = fields.Integer('Total Products Synced', readonly=True)
    lens_count = fields.Integer('Lens Products', readonly=True)
    opts_count = fields.Integer('Optical Frames', readonly=True)
    other_count = fields.Integer('Other Products', readonly=True)

    def _get_config(self):
        return {
            'base_url': os.getenv('SPRING_BOOT_BASE_URL', 'https://localhost:8443'),
            'login_endpoint': os.getenv('API_LOGIN_ENDPOINT', '/api/auth/login'),
            'products_endpoint': os.getenv('API_PRODUCTS_ENDPOINT', '/api/xnk/products'),
            'username': os.getenv('DEFAULT_VNOPTIC_USERNAME', 'admin'),
            'password': os.getenv('DEFAULT_VNOPTIC_PASSWORD', ''),
            'ssl_verify': os.getenv('SSL_VERIFY', 'False').lower() == 'true',
            'login_timeout': int(os.getenv('LOGIN_TIMEOUT', '30')),
            'api_timeout': int(os.getenv('API_TIMEOUT', '300')),
        }

    def _login_spring_boot(self):
        try:
            config = self._get_config()  # ← THÊM DÒNG NÀY

            login_url = f"{config['base_url']}{config['login_endpoint']}"

            _logger.info(f"Logging into Spring Boot as: {config['username']}")

            response = requests.post(
                login_url,
                data={
                    'username': config['username'],
                    'password': config['password']
                },
                verify=config['ssl_verify'],
                timeout=config['login_timeout']
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')

                if not token:
                    raise UserError(_('Login failed: Token is null'))

                _logger.info(f"✅ Got token from Spring Boot")
                return token
            else:
                raise UserError(_('Login failed: %s - %s') % (response.status_code, response.text[:200]))

        except requests.exceptions.RequestException as e:
            raise UserError(_('Connection error: %s') % str(e))

    def sync_products_from_springboot(self):
        for record in self:
            try:
                config = record._get_config()

                _logger.info("=" * 60)
                _logger.info("Starting product synchronization...")

                token = record._login_spring_boot()

                api_url = f"{config['base_url']}{config['products_endpoint']}"

                _logger.info(f"Fetching products from: {api_url}")

                response = requests.get(
                    api_url,
                    verify=config['ssl_verify'],
                    timeout=(30, config['api_timeout']),
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                )

                if response.status_code != 200:
                    raise UserError(f'API error {response.status_code}')

                # Parse response
                api_response = response.json()

                _logger.info(f"Response type: {type(api_response)}")

                # ==================== XỬ LÝ RESPONSE ====================
                products_data = None

                if isinstance(api_response, dict):
                    # Case 1: {"products": "[{...},{...}]"} - STRING chứa JSON
                    if 'products' in api_response:
                        products_str = api_response['products']
                        _logger.info(f"Found 'products' key, type: {type(products_str)}")

                        if isinstance(products_str, str):
                            # Parse string JSON thành array
                            import json
                            products_data = json.loads(products_str)
                            _logger.info(f"Parsed products string to array: {len(products_data)} items")
                        elif isinstance(products_str, list):
                            products_data = products_str
                            _logger.info(f"Products already array: {len(products_data)} items")

                    # Case 2: {"content": [...]} - Paginated
                    elif 'content' in api_response:
                        products_data = api_response['content']
                        _logger.info(f"Found 'content' key: {len(products_data)} items")

                    # Case 3: {"data": [...]}
                    elif 'data' in api_response:
                        products_data = api_response['data']
                        _logger.info(f"Found 'data' key: {len(products_data)} items")

                # Case 4: Direct array
                elif isinstance(api_response, list):
                    products_data = api_response
                    _logger.info(f"Direct array: {len(products_data)} items")

                # Kiểm tra có data không
                if not products_data or not isinstance(products_data, list):
                    raise UserError(_('Cannot extract products from API response'))

                if len(products_data) == 0:
                    raise UserError(_('API returned 0 products'))

                _logger.info(f"Processing {len(products_data)} products...")

                # Process products
                success, failed, stats = record._process_and_categorize_products(products_data)

                # Cập nhật kết quả
                record.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_status': 'success',
                    'total_synced': success,
                    'lens_count': stats['lens'],
                    'opts_count': stats['opts'],
                    'other_count': stats['other'],
                    'sync_log': f"""
    ✅ SYNC COMPLETED!

    Total: {success} synced, {failed} failed

    Categories:
    Lens: {stats['lens']}
    Frames: {stats['opts']}
    Others: {stats['other']}

    Date: {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                })

                self.env.cr.commit()

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Success'),
                        'message': f'Synced {success} products!',
                        'type': 'success',
                    }
                }

            except Exception as e:
                error_msg = f"Sync error: {str(e)}"
                _logger.error(error_msg)
                _logger.exception("Full traceback:")

                record.write({
                    'sync_status': 'error',
                    'sync_log': error_msg
                })
                raise UserError(_(error_msg))

    def _process_and_categorize_products(self, products_data):
        """Xử lý và TỰ ĐỘNG PHÂN LOẠI sản phẩm theo groupTypedto"""
        Template = self.env['product.template']
        success = 0
        failed = 0

        # Thống kê theo loại
        stats = {
            'lens': 0,  # Mắt
            'opts': 0,  # Gọng
            'other': 0  # Khác
        }

        if not isinstance(products_data, list):
            raise UserError("Products data must be an array")

        _logger.info(f"Processing {len(products_data)} products...")

        for idx, p in enumerate(products_data, 1):
            try:
                with self.env.cr.savepoint():

                    if not isinstance(p, dict):
                        _logger.warning(f"Product {idx}: Invalid type")
                        failed += 1
                        continue

                    cid = p.get('cid') or ''
                    if not cid:
                        _logger.warning(f"Product {idx}: No CID")
                        failed += 1
                        continue

                    name = p.get('fullname') or 'Unknown Product'

                    # ==================== PHẦN PHÂN LOẠI TỰ ĐỘNG ====================
                    groupdto = p.get('groupdto') or {}
                    group_type_dto = groupdto.get('groupTypedto') or {}
                    group_type_name = group_type_dto.get('name') or 'Khác'  # "Mắt"/"Gọng"/"Khác"
                    group_name = groupdto.get('name') or 'All Products'

                    # Map sang category tiếng Anh
                    category_mapping = {
                        'Mắt': 'Lens Products',
                        'Gọng': 'Optical Frames',
                        'Khác': 'Accessories'
                    }

                    main_category = category_mapping.get(group_type_name, 'Accessories')

                    # Map sang product_type cho model vnoptic_product
                    product_type_mapping = {
                        'Mắt': 'lens',
                        'Gọng': 'opt',
                        'Khác': 'accessory'
                    }
                    product_type = product_type_mapping.get(group_type_name, 'accessory')

                    # Đếm theo loại
                    if group_type_name == 'Mắt':
                        stats['lens'] += 1
                    elif group_type_name == 'Gọng':
                        stats['opts'] += 1
                    else:
                        stats['other'] += 1

                    # Tạo category hierarchy: Parent / Child
                    categ_id = self._get_or_create_category(group_name, parent_name=main_category)
                    # =================================================================

                    _logger.info(f"[{idx}/{len(products_data)}] {cid} → {group_type_name} / {group_name}")

                    # Các thông tin khác
                    brand_id = self._get_or_create_brand(
                        (p.get('tmdto') or {}).get('cid'),
                        (p.get('tmdto') or {}).get('name')
                    )

                    country_id = self._get_or_create_country(
                        (p.get('codto') or {}).get('cid'),
                        (p.get('codto') or {}).get('name')
                    )

                    warranty_id = self._get_or_create_warranty(p.get('warrantydto'))
                    uom_id, uom_po_id = self._get_or_create_uom(p.get('unit') or 'Unit')

                    tax_percent = float(p.get('tax') or 0)
                    tax_id = self._get_or_create_tax(tax_percent)
                    taxes_ids = [(6, 0, [tax_id])] if tax_id else False

                    # Prices
                    rt_price = float(p.get('rtPrice') or 0)
                    ws_price = float(p.get('wsPrice') or 0)
                    ct_price = float(p.get('ctPrice') or 0)
                    or_price = float(p.get('orPrice') or 0)

                    tmpl = Template.search([('default_code', '=', cid)], limit=1)

                    vals = {
                        'name': name,
                        'default_code': cid,
                        'type': 'product',
                        'categ_id': categ_id,
                        'uom_id': uom_id,
                        'uom_po_id': uom_po_id,
                        'list_price': rt_price,
                        'standard_price': or_price,
                        'taxes_id': taxes_ids,

                        # Thêm product_type để phân loại đúng
                        'product_type': product_type,  # 'lens', 'opt', hoặc 'accessory'

                        'x_eng_name': p.get('engName') or '',
                        'x_trade_name': p.get('tradeName') or '',
                        'x_note_long': p.get('note') or '',
                        'x_uses': p.get('uses') or '',
                        'x_guide': p.get('guide') or '',
                        'x_warning': p.get('warning') or '',
                        'x_preserve': p.get('preserve') or '',

                        'x_cid_ncc': p.get('cidNcc') or '',
                        'x_accessory_total': int(p.get('accessoryTotal') or 0),
                        'x_status_name': (p.get('statusProductdto') or {}).get('name') or '',
                        'x_tax_percent': tax_percent,

                        'x_currency_zone_code': (p.get('currencyZoneDTO') or {}).get('cid') or '',
                        'x_currency_zone_value': float((p.get('currencyZoneDTO') or {}).get('value') or 0),

                        'x_ws_price': ws_price,
                        'x_ct_price': ct_price,
                        'x_or_price': or_price,

                        'x_group_type_name': group_type_name,  # Lưu "Mắt"/"Gọng"/"Khác"

                        'x_country_id': country_id or False,
                        'x_brand_id': brand_id or False,
                        'x_warranty_id': warranty_id or False,
                    }

                    if tmpl:
                        tmpl.write(vals)
                    else:
                        tmpl = Template.create(vals)

                    # Supplier
                    supplier_details = ((p.get('supplierdto') or {}).get('supplierDetailDTOS')) or []
                    if supplier_details:
                        partner = self._get_or_create_supplier(supplier_details[0])
                        if partner:
                            self._ensure_sellerinfo(tmpl, partner, ws_price or or_price)

                    # Image
                    img_url = p.get('imageUrl') or ''
                    if img_url and 'default.png' not in img_url:
                        try:
                            img_b64 = self._download_image(img_url)
                            if img_b64:
                                tmpl.write({'image_1920': img_b64})
                        except Exception as img_error:
                            _logger.warning(f"Image error for {cid}: {img_error}")

                    success += 1

            except Exception as e:
                failed += 1
                _logger.exception(f"Error processing product {idx}: {e}")
                continue

        _logger.info(f"✅ Sync completed: {success} OK, {failed} failed")
        _logger.info(f"📊 Stats: Lens={stats['lens']}, Opts={stats['opts']}, Other={stats['other']}")

        return success, failed, stats

    # ==================== HELPER METHODS ====================

    def _get_or_create_category(self, category_name, parent_name=None):
        Category = self.env['product.category']

        if not category_name:
            return self.env.ref('product.product_category_all').id

        parent_id = False
        if parent_name:
            parent = Category.search([('name', '=', parent_name)], limit=1)
            if not parent:
                try:
                    parent = Category.create({'name': parent_name})
                except:
                    pass
            if parent:
                parent_id = parent.id

        domain = [('name', '=', category_name)]
        if parent_id:
            domain.append(('parent_id', '=', parent_id))

        category = Category.search(domain, limit=1)

        if category:
            return category.id

        try:
            vals = {'name': category_name}
            if parent_id:
                vals['parent_id'] = parent_id
            category = Category.create(vals)
            return category.id
        except Exception as e:
            _logger.warning(f"Error creating category {category_name}: {e}")
            return self.env.ref('product.product_category_all').id

    def _get_or_create_brand(self, brand_cid, brand_name):
        """Tạo hoặc lấy brand"""
        if not brand_cid or not brand_name:
            return False

        Brand = self.env['xnk.brand']  # ← SỬA: x_brand → xnk.brand
        brand = Brand.search([('code', '=', brand_cid)], limit=1)  # ← SỬA: x_cid → code

        if brand:
            return brand.id

        try:
            brand = Brand.create({
                'name': brand_name,  # ← SỬA: x_name → name
                'code': brand_cid  # ← SỬA: x_cid → code
            })
            return brand.id
        except Exception as e:
            _logger.warning(f"Error creating brand {brand_name}: {e}")
            return False

    def _get_or_create_country(self, country_cid, country_name):
        """Tạo hoặc lấy country"""
        if not country_cid or not country_name:
            return False

        Country = self.env['xnk.country']  # ← xnk.country
        country = Country.search([('code', '=', country_cid)], limit=1)

        if country:
            return country.id

        try:
            country = Country.create({
                'name': country_name,
                'code': country_cid
            })
            return country.id
        except Exception as e:
            _logger.warning(f"Error creating country {country_name}: {e}")
            return False

    def _get_or_create_warranty(self, warranty_dto):
        """Tạo hoặc lấy warranty"""
        if not warranty_dto or not isinstance(warranty_dto, dict):
            return False

        warranty_cid = warranty_dto.get('cid')
        warranty_name = warranty_dto.get('name')

        if not warranty_cid or not warranty_name:
            return False

        Warranty = self.env['xnk.warranty']  # ← SỬA: x_warranty → xnk.warranty
        warranty = Warranty.search([('code', '=', warranty_cid)], limit=1)  # ← SỬA: x_cid → code

        if warranty:
            return warranty.id

        try:
            warranty = Warranty.create({
                'name': warranty_name,  # ← SỬA: x_name → name
                'code': warranty_cid,  # ← SỬA: x_cid → code
                'description': warranty_dto.get('description', ''),  # ← Giữ nguyên
                'value': int(warranty_dto.get('value', 0))  # ← Giữ nguyên
            })
            return warranty.id
        except Exception as e:
            _logger.warning(f"Error creating warranty {warranty_name}: {e}")
            return False

    def _get_or_create_uom(self, unit_name):
        """Tạo hoặc lấy UOM"""
        Uom = self.env['uom.uom']

        uom = Uom.search([('name', '=', unit_name)], limit=1)

        if uom:
            return uom.id, uom.id

        try:
            category = self.env.ref('uom.product_uom_categ_unit')
            uom = Uom.create({
                'name': unit_name,
                'category_id': category.id,
                'uom_type': 'reference',
                'rounding': 0.01
            })
            return uom.id, uom.id
        except Exception as e:
            _logger.warning(f"Error creating UOM {unit_name}: {e}")
            default_uom = self.env.ref('uom.product_uom_unit')
            return default_uom.id, default_uom.id

    def _get_or_create_tax(self, tax_percent):
        """Tạo hoặc lấy tax"""
        if not tax_percent or tax_percent == 0:
            return False

        Tax = self.env['account.tax']

        tax_name = f"Tax {tax_percent}%"
        tax = Tax.search([
            ('name', '=', tax_name),
            ('type_tax_use', '=', 'sale')
        ], limit=1)

        if tax:
            return tax.id

        try:
            tax = Tax.create({
                'name': tax_name,
                'amount': tax_percent,
                'amount_type': 'percent',
                'type_tax_use': 'sale'
            })
            return tax.id
        except Exception as e:
            _logger.warning(f"Error creating tax {tax_name}: {e}")
            return False

    def _get_or_create_supplier(self, supplier_detail):
        """Tạo hoặc lấy supplier"""
        if not supplier_detail or not isinstance(supplier_detail, dict):
            return False

        supplier_cid = supplier_detail.get('cid')
        supplier_name = supplier_detail.get('name')

        if not supplier_cid or not supplier_name:
            return False

        Partner = self.env['res.partner']

        partner = Partner.search([('ref', '=', supplier_cid)], limit=1)

        if partner:
            return partner

        try:
            partner = Partner.create({
                'name': supplier_name,
                'ref': supplier_cid,
                'is_company': True,
                'supplier_rank': 1,
                'phone': supplier_detail.get('phone', ''),
                'email': supplier_detail.get('mail', ''),
                'street': supplier_detail.get('address', '')
            })
            return partner
        except Exception as e:
            _logger.warning(f"Error creating supplier {supplier_name}: {e}")
            return False

    def _ensure_sellerinfo(self, product_tmpl, partner, price):
        """Tạo hoặc update supplier info"""
        if not partner:
            return

        SellerInfo = self.env['product.supplierinfo']

        seller = SellerInfo.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if seller:
            seller.write({'price': price})
        else:
            try:
                SellerInfo.create({
                    'partner_id': partner.id,
                    'product_tmpl_id': product_tmpl.id,
                    'price': price,
                    'min_qty': 1
                })
            except Exception as e:
                _logger.warning(f"Error creating supplier info: {e}")

    def _download_image(self, image_url):
        """Download image từ URL và convert sang base64"""
        if not image_url or 'default.png' in image_url:
            return False

        try:
            if image_url.startswith('/api/files/'):
                image_url = f'https://localhost:8443{image_url}'

            response = requests.get(image_url, verify=False, timeout=10)

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))

                if img.width > 1920 or img.height > 1920:
                    img.thumbnail((1920, 1920), Image.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format=img.format or 'PNG')
                img_b64 = base64.b64encode(buffer.getvalue())

                return img_b64
            else:
                return False

        except Exception as e:
            _logger.warning(f"Error downloading image {image_url}: {e}")
            return False

    def test_api_connection(self):
        try:
            config = self._get_config()  # ← THÊM
            token = self._login_spring_boot()

            api_url = f"{config['base_url']}{config['products_endpoint']}"  # ← SỬA

            response = requests.get(
                api_url,
                verify=config['ssl_verify'],  # ← SỬA
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

            if response.status_code == 200:
                data = response.json()
                count = len(data.get('content', [])) if isinstance(data, dict) else len(data)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Success'),
                        'message': f'Login OK! Found {count} products available.',
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('API error: %s') % response.status_code)

        except Exception as e:
            raise UserError(_('Test failed: %s') % str(e))
