from setuptools import setup, find_packages

def readme():
  with open('README.md', 'r') as f:
    return f.read()

setup(
  name='Flatel',
  version='0.0.2',
  author='DepyXa',
  author_email='dere96632@gmail.com',
  description='Flastel – Telegram Bot API.',
  long_description=readme(),
  long_description_content_type='text/html',
  url='https://github.com/DepyXa/Flastel',
  packages=find_packages(),
  install_requires=[
    'requests>=2.25.1'
  ],
  classifiers=[
    'Programming Language :: Python :: 3.11',
    'License :: GNU General ::  GPL-3.0 license',
    'Operating System :: OS Independent'
  ],
  keywords='Telegram Bot API ',
  project_urls={
    'GitHub': 'https://github.com/DepyXa'
  },
  python_requires='>=3.6'
)
