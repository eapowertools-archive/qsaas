from distutils.core import setup
setup(
    name='qsaas',
    packages=['qsaas'],
    version='0.0.1',
    license='GPL-3.0',
    description='A wrapper for the Qlik Sense Enterprise SaaS APIs.',
    author='Daniel Pilla',
    author_email='daniel.b.pilla@gmail.com',
    url='https://github.com/eapowertools/qsaas',
    download_url='https://github.com/eapowertools/qsaas/archive/v_001.tar.gz',
    keywords=['Qlik', 'API', 'REST', 'WRAPPER', 'QSAAS', 'QSESAAS'],
    install_requires=[
        'requests',
        'aiohttp',
        'asyncio',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
