from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import CustomUser


def dtime():
    return timezone.now() + timedelta(hours=3)

# Order model
class Order(models.Model):
    id = models.AutoField(primary_key=True)
    regdate = models.DateTimeField(default=dtime)
    customer = models.CharField(max_length=255)
    phone = models.CharField(max_length=10)
    duedate = models.DateField()
    price = models.FloatField()
    description = models.TextField(null=True, default=None)
    status = models.BooleanField(default = False)
    deleted = models.BooleanField(default = False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='user')
    objects = models.Manager()
    
    def __str__(self):
        return str(self.customer)


# Purchases model
class Purchase(models.Model):
    id = models.AutoField(primary_key=True)
    regdate = models.DateTimeField(default=dtime)
    purchasedate = models.DateField(null=True, default=None)
    product = models.CharField(max_length=255)
    supplier = models.CharField(max_length=255)
    payment = models.CharField(max_length=3)
    paid = models.BooleanField()
    cost = models.FloatField()
    extra_cost = models.FloatField(default=0.0)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(default = False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='buyer')
    objects = models.Manager()
    
    def __str__(self):
        return str(self.product)