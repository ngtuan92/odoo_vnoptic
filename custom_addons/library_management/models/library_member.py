from odoo import models, fields


class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Thành viên thư viện'

    name = fields.Char('Họ và tên', required=True)
    member_id = fields.Char('Mã thành viên', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Số điện thoại')
    address = fields.Text('Địa chỉ')
    state = fields.Selection([
        ('active', 'Hoạt động'),
        ('suspended', 'Đình chỉ'),
        ('expired', 'Hết hạn')
    ], string='Trạng thái', default='active')
    membership_type = fields.Selection([
        ('student', 'Sinh viên'),
        ('teacher', 'Giáo viên'),
        ('staff', 'Nhân viên'),
        ('vip', 'VIP')
    ], string='Loại thành viên', required=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('Other', 'Khác')
    ], string='Giới tính')
    join_date = fields.Date('Ngày gia nhập', default=fields.Date.today)
    expiry_date = fields.Date('Ngày hết hạn')
    membership_fee = fields.Float('Phí thành viên', default=0.0)

    def action_activate(self):
        for record in self:
            record.state = 'active'
        return True

    def action_suspend(self):
        for record in self:
            record.state = 'suspended'
        return True
