from setuptools import setup, find_packages

setup(
    name='aiozmq-heartbeat',
    version='0.0.1',
    description='Simple heartbeat implementation on top of aiozmq.rpc',
    author='Mikhail Lukyanchenko',
    author_email='ml@akabos.com',
    url='https://github.com/akabos/aiozmq-heartbeat',
    packages=find_packages(),
    include_package_data=False,
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        'pyzmq>=15.0.0',
        'msgpack-python>=0.4.6',
        'aiozmq>=0.7',
    ]
)
