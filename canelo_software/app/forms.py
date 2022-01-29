from dataclasses import field
from django.forms import ModelForm, DateInput
from .models import Agricultor, ActualizacionPrecio

#Form para la agregar y editar datos de los agricultores
class AgricultorForm(ModelForm):
    class Meta():
        model = Agricultor
        fields = '__all__'
        widgets = {
            "fecha_primera_entrevista": DateInput(attrs={'class':'form-control', 'type':'date'}),
        }

#Form para subir nuevos archivos de precios
class ActualizacionPrecioForm(ModelForm):
    class Meta():
        model = ActualizacionPrecio
        fields = '__all__'
        exclude = ['fecha_subida']