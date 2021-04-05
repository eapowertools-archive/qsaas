from setuptools import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    name='qsaas',
    packages=['qsaas'],
    version='1.2.0',
    license='GPL-3.0',
    description='A Python wrapper for the Qlik Sense Enterprise SaaS APIs.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Daniel Pilla',
    author_email='daniel.b.pilla@gmail.com',
    url='https://github.com/eapowertools/qsaas',
    download_url='https://github.com/eapowertools/qsaas/archive/v1.2.0.tar.gz',
    keywords=['Qlik', 'API', 'REST', 'Sense', 'QSAAS', 'QSESAAS'],
    install_requires=[
        'requests',
        'requests-toolbelt',
        'aiohttp',
        'asyncio',
    ],
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
