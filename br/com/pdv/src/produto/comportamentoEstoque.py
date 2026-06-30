from abc import ABC, abstractmethod
class ComportamentoEstoque(ABC):
   
    @abstractmethod
    def saida(self, quantidade: int):
        pass

    def entrada(self, quantidade: int):
        pass

    @abstractmethod
    def atualizar(self):
        pass

    @abstractmethod
    def vizualizar(self) -> dict:
        pass