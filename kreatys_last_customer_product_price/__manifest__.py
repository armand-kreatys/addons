{
    'name': 'Kreatys Last Customer Product Price',
    'description': 'Module pour ajouter le dernier prix pratiqué à la ligne de devis',
    'author': 'kreatys-armand',
    'version': '1.0',
    'category': 'KREATYS',
    'installable': True,
    'application': True,
    'depends': ['sale', 'account'],
    'data': [
        'views/sale_order_line.xml',
    ],
}
