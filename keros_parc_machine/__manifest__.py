{
    'name': 'Parc Machine',
    'version': '1.0',
    'summary': 'Gestion du parc machine',
    'description': 'Module pour gérer le parc machine.',
    'author': 'armand-kreatys',
    'website': 'https://integrateur-odoo.kreatys.com',
    'category': 'KREATYS',
    'depends': ['base', 'stock', 'maintenance', 'sale_management', 'purchase', 'helpdesk', 'repair'],
    'data': [
        'security/ir.model.access.csv',
        'data/parc_machine_data.xml',
        'views/res_partner_views.xml',
        'views/parc_machine_views.xml',
    ],
    'installable': True,
    'application': True,
}
