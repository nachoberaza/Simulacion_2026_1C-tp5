class RecursoMedico:

    def __init__(self, cantidad):

        self.cantidad_total = cantidad
        self.ocupados = 0

    def hay_disponible(self):

        return self.ocupados < self.cantidad_total

    def ocupar(self):

        self.ocupados += 1

    def liberar(self):

        self.ocupados -= 1
