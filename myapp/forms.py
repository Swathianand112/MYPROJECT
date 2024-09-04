from django import forms

class UploadFileForm(forms.Form):
    crf_file = forms.FileField(label='Upload CRF File')
    email_file = forms.FileField(label='Upload Email File')
