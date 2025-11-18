{
    'name': "Library Management",
    'summary': """Hệ thống quản lý thư viện""",
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/library_book_views.xml',
        'views/library_member_views.xml',
        'views/library_loan_views.xml',
        # 'data/library_demo.xml',
    ],

    'installable': True,
    'application': True,
}
