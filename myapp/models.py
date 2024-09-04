from django.db import models
class Account(models.Model):
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

class CRF_Document(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    link_alias = models.TextField()
    link_description = models.TextField()
    link_location = models.URLField()
    base_url = models.URLField()

    def __str__(self):
        return f"{self.account.name} - {self.link_alias}"

    class Meta:
        verbose_name = "CRF Document"
        verbose_name_plural = "CRF Documents"

class CRF_Validation_Result(models.Model):
    crf_document = models.ForeignKey(CRF_Document, on_delete=models.CASCADE)
    link_alias_match = models.JSONField()
    link_url_match = models.JSONField()
    pass_validation = models.BooleanField(default=False)

    def __str__(self):
        return f"Validation Result for {self.crf_document.link_alias} - Pass: {self.pass_validation}"

    class Meta:
        verbose_name = "CRF Validation Result"
        verbose_name_plural = "CRF Validation Results"