# -*- coding: utf-8 -*-
from lettuce import step

@step(u'I am subscribed')
def i_am_subscribed(step):
    assert False, 'This step must be implemented'
@step(u'a post is published')
def post_is_published(step):
    assert False, 'This step must be implemented'
@step(u'I get an email')
def get_an_email(step):
    assert False, 'This step must be implemented'

