# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Asks(models.Model):
    id_pair = models.IntegerField(db_column='id_pair', blank=True, null=True)  # Field name made lowercase.
    price = models.TextField(db_column='Price', blank=True, null=True)  # Field name made lowercase.
    timestamp = models.TextField(db_column='TimeStamp', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    volume = models.TextField(db_column='Volume', blank=True, null=True)  # Field name made lowercase.



class Bids(models.Model):
    volume = models.TextField(db_column='Volume', blank=True, null=True)  # Field name made lowercase.
    price = models.TextField(db_column='Price', blank=True, null=True)  # Field name made lowercase.
    timestamp = models.TextField(db_column='TimeStamp', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    id_pair = models.IntegerField(db_column='id_pair', blank=True, null=True)  # Field name made lowercase.



class Pairs(models.Model):
    id_pair = models.AutoField(primary_key=True)
    buy_pair = models.CharField(max_length=100)
    sell_pair = models.CharField(max_length=100)


class Bots(models.Model):
    robot = models.AutoField(primary_key=True)
    market_orders = models.BooleanField(null=False)
    freq = models.DecimalField(max_digits=10, decimal_places=3)
    max_orders = models.IntegerField(null=True)

class Trades(models.Model):
    pair = models.ForeignKey(Pairs, on_delete=models.DO_NOTHING)
    user = models.IntegerField(null=False)
    timestamp = models.TextField()
    volume = models.FloatField()
    price = models.FloatField()
    buy = models.BooleanField(default=True)

class LocalBids(models.Model):
    pair = models.ForeignKey(Pairs, on_delete=models.DO_NOTHING)
    user = models.IntegerField(null=False)
    timestamp = models.TextField()
    volume = models.FloatField()
    price = models.FloatField()
    buy = models.BooleanField(default=True)
