{
    'name': "My pet",
    'summary': """My pet model""",
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/my_pet_views.xml',
        'wizard/batch_update.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mypet/static/src/xml/*.xml',
            'mypet/static/src/js/*.js',
        ],
    },
    'installable': True,
    'application': True,
}
