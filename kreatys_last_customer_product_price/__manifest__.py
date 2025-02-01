{
    'name': 'Kreatys Last Customer Product Price',
    'description': 'Module pour ajouter le dernier prix pratiqué à la ligne de devis',
    'author': 'kreatys-armand',
    'version': '18.0',
    'category': 'KREATYS',
    'website': 'https://integrateur-odoo.kreatys.com',
    'installable': True,
    'application': True,
    'depends': ['sale', 'account'],
    'data': [
        'views/sale_order_line.xml',
    ],
}
