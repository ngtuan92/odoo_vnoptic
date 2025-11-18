from odoo import models, fields


class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Mượn trả sách'

    name = fields.Char('Mã phiếu mượn', required=True, default='/')
    member_id = fields.Many2one('library.member', string='Thành viên', required=True)
    book_id = fields.Many2one('library.book', string='Sách', required=True)
    loan_date = fields.Date('Ngày mượn', default=fields.Date.today, required=True)
    due_date = fields.Date('Ngày hẹn trả', required=True)
    state = fields.Selection([
        ('borrowed', 'Đang mượn'),
        ('returned', 'Đã trả'),
        ('overdue', 'Quá hạn')
    ], string='Trạng thái', default='borrowed')
