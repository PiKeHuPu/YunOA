#!/user/bin/env python
#-*- coding:utf-8 -*-
'''
@author  : Evan
@desc    :
'''

from django import forms
from django.contrib.auth import get_user_model
from .models import Bulletin

User = get_user_model()

class BulletinUpdateForm(forms.ModelForm):
    class Meta:
        model = Bulletin
        fields = ['file_content']

class BulletinCreateForm(forms.ModelForm):
    class Meta:
        model = Bulletin
        fields = ['title', 'type', 'status', 'file_content']