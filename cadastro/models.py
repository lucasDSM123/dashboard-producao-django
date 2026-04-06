from django.db import models

class Material(models.Model):
    Obra = models.CharField(max_length=100, null=True, blank=True)
    Codigo = models.CharField(max_length=100)
    Descricao = models.TextField()
    Quantidade = models.IntegerField()
    # Alterado para CharField porque seus lotes têm letras e números
    Lote = models.CharField(max_length=100) 
    # NOVO CAMPO: Essencial para a lógica de valores que criamos
    Preco_Unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.Codigo} - {self.Descricao}"

    # Essa função facilita muito a vida no HTML para calcular o subtotal
    @property
    def total_item(self):
        return self.Quantidade * self.Preco_Unitario