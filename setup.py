from setuptools import find_packages, setup

setup(
    name='minerva',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask==1.1.2',
        'SQLAlchemy==1.3.18',
        'Werkzeug==1.0.1',
        'barcode_generator==0.1rc15',
        'click==7.1.2',
        'babel',
        'ortools',
        'pdfkit==0.6.1',
        'geopy',
        'python-barcode==0.13.1',
        'Pillow',
        'python-dotenv==0.14.0',
        'qrcode==6.1',
        'requests==2.24.0',
        'sendgrid==6.4.4',
        'yagmail==0.11.224',
        'pandas',
        'xlrd==1.2.0',
        'usaddress',
        'StyleFrame'
    ],
)
