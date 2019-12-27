from django import forms

class UserBids(forms.Form):
    quantity = forms.CharField(label='Quantity', max_length=100)
    price = forms.CharField(label='Price', max_length=100)
    pair = forms.CharField(label='Pair', max_length=100)
    buy_sell = forms.BooleanField(label='Buy')