from setuptools import find_packages, setup

package_name = 'chess_planner'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ricky',
    maintainer_email='ricardometral2005@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            f'chess_planner_node = {package_name}.planner:main',
            f'lichess_planner_node = {package_name}.lichess_planner:main'
        ],
    },
)
