from django import forms
from .models import Order, Purchase


# new order registartion form
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'phone', 'price', 'duedate', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False

    def clean_customer(self):
        customer = self.cleaned_data.get('customer').strip().capitalize()
        if len(customer) < 3:
            raise forms.ValidationError("Customer name is too short.")
        return customer
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone').strip()
        if phone and not phone.isdigit():
            raise forms.ValidationError("Please use a 10-digit phone number.")
        if phone and len(phone) != 10:
            raise forms.ValidationError("Please use a 10-digit phone number.")
        return phone

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        return None if description in ("", "-") else description


# new purchase registartion form
class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['purchasedate', 'product', 'supplier', 'payment', 'paid', 'cost', 'extra_cost', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid'].required = False
        self.fields['description'].required = False

    def clean_product(self):
        product = self.cleaned_data.get('product').strip()
        if len(product) < 3:
            raise forms.ValidationError("Item name is too short.")
        return product
    
    def clean_supplier(self):
        supplier = self.cleaned_data.get('supplier').strip()
        if len(supplier) < 3:
            raise forms.ValidationError("Supplier name is too short.")
        return supplier
    
    def clean_extra_cost(self):
        extra_cost = self.cleaned_data.get('extra_cost')
        return 0.0 if extra_cost == "" else extra_cost

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        return None if description in ("", "-") else description
