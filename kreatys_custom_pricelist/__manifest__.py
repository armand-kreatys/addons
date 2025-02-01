{
    'name': 'Kreatys Custom Pricelist',
    'version': '18.0',
    'summary': 'Calcul le prix final d\'un produit en fonction de toutes les règles de tarification',
    'description': """
        Ce module calcule le prix final d'un produit en évaluant toutes les règles de tarification applicables,
        y compris les règles spécifiques au produit, les règles basées sur la catégorie et les listes de prix alternatives.
    """,
    'author': 'kreatys-armand',
    'website': 'https://integrateur-odoo.kreatys.com',
    'category': 'KREATYS',
    'depends': ['product', 'sale'],
    'installable': True,
    'application': True,
}
