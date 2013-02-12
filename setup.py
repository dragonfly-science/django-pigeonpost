from distutils.core import setup

setup(name='pigeonpost',
      version='0.1.9',
      description='Buffered delivery of emails in Django',
      author='Edward Abraham',
      author_email='edward@dragonfly.co.nz',
      url='https://github.com/dragonfly-science/django-pigeonpost',
      packages=['pigeonpost','pigeonpost.management', 'pigeonpost.management.commands'],
      scripts = ['pigeonpost/bin/deploy_pigeons'],
     )
