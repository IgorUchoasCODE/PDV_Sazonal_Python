from typing import Protocol, runtime_checkable

@runtime_checkable
class IValidador(Protocol):

    
    def getNome(self) -> str:
        pass

   
    def validar(self, valor: str) -> bool:
        pass

   
    def parse(self, valor: str) -> str:
        pass