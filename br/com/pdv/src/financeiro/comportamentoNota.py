from abc import ABC, abstractmethod

class ComportamentoNota(ABC):

    @abstractmethod
    def nota (self, id:int,  ):
        pass