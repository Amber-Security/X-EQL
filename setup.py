from setuptools import setup, find_packages  
  
setup(  
    name='holmes',  
    version='v1.1.1-alpha',  
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[  
        # 这里列出你的项目依赖  
    ],  
    author='AmberSecurity',  
    author_email='dontbuyapie@gmail.com',
    description='holmes engine',
    url='https://github.com/Amber-Security/Holmes',
)