{
    'name': 'Work permissions',   
    'version': '1.0',
    'category': 'MyAddons/WorkPermissions',
    'summary': 'List of workers work permissions',
    'description': "",
    'depends': [
        'base'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/permission_request_type_views.xml',
        'views/permission_menus.xml'
        ],
    'application': True,
}