# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class tradeview_asks(models.Model):
    price = models.TextField(db_column='Price', blank=True, null=True)  # Field name made lowercase.
    volume = models.TextField(db_column='Volume', blank=True, null=True)  # Field name made lowercase.
    timestamp = models.TextField(db_column='TimeStamp', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    id_pair_id = models.IntegerField(db_column='ID_pair_id', blank=True, null=True)  # Field name made lowercase.

class tradeview_bids(models.Model):
    volume = models.TextField(db_column='Volume', blank=True, null=True)  # Field name made lowercase.
    price = models.TextField(db_column='Price', blank=True, null=True)  # Field name made lowercase.
    timestamp = models.TextField(db_column='TimeStamp', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    id_pair_id = models.IntegerField(db_column='ID_pair_id', blank=True, null=True)  # Field name made lowercase.

class tradeview_pairs(models.Model):
    id_pair = models.AutoField(primary_key=True)
    buy_pair = models.CharField(max_length=100)
    sell_pair = models.CharField(max_length=100)

