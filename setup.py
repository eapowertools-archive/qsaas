from distutils.core import setup


def readme():
    """ print long description """
    with open('README.md') as f:
        long_descrip = f.read()
    return long_descrip


setup(
    name='qsaas',
    packages=['qsaas'],
    version='0.0.2',
    license='GPL-3.0',
    description='A wrapper for the Qlik Sense Enterprise SaaS APIs.',
    long_description=readme(),
    long_description_content_type="text/markdown",
    author='Daniel Pilla',
    author_email='daniel.b.pilla@gmail.com',
    url='https://github.com/eapowertools/qsaas',
    download_url='https://github.com/eapowertools/qsaas/archive/v0.0.2-alpha.tar.gz',
    keywords=['Qlik', 'API', 'REST', 'Sense', 'QSAAS', 'QSESAAS'],
    install_requires=[
        'requests',
        'aiohttp',
        'asyncio',
    ],
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
