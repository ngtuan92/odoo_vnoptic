from odoo import models, fields, api


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Sách thư viện'

    name = fields.Char('Tên sách', required=True)
    author = fields.Char('Tác giả')
    isbn = fields.Char('Mã ISBN')
    category = fields.Selection([
        ('fiction', 'Tiểu thuyết'),
        ('science', 'Khoa học'),
        ('technology', 'Công nghệ'),
        ('other', 'Khác')
    ], string='Thể loại', default='other')

    total_copies = fields.Integer('Tổng số bản', default=1)
    available_copies = fields.Integer('Số bản có sẵn', default=1)
    price = fields.Float('Giá', default=0.0)
    total_value = fields.Float('Tổng giá trị', compute='_compute_total_value', store=True)

    state = fields.Selection([
        ('available', 'Có sẵn'),
        ('borrowed', 'Đã mượn'),
        ('maintenance', 'Bảo trì'),
        ('lost', 'Mất')
    ], string='Trạng thái', default='available')

    def action_set_available(self):
        for record in self:
            record.state = 'available'

    def action_set_maintenance(self):
        for record in self:
            record.state = 'maintenance'

    def action_set_borrowed(self):
        for record in self:
            record.state = 'borrowed'

    @api.depends('price', 'total_copies')
    def _compute_total_value(self):
        for record in self:
            record.total_value = record.price * record.total_copies

    _sql_constraints = [('unique_isbn', 'UNIQUE(isbn)', 'ISBN ko đc trùng nhau'), ]
