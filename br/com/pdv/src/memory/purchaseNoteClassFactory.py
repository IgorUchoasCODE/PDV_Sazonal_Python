import sqlite3
from br.com.pdv.src.memory.productClassFactory import ProductClassFactory
from br.com.pdv.src.memory.supplierClassFactory import SupplierClassFactory
from br.com.pdv.src.BDD.queryEnum import DB
from br.com.pdv.src.financeiro.notaCompra import NotaCompra

class PurchaseNoteClassFactory:
    __purchaseNote:dict[int,NotaCompra] = {}

    @classmethod
    def fabricar(cls, id:int) -> NotaCompra:
        if id in cls.__purchaseNote:
            return cls.__purchaseNote[id]
        
        try:
            etqEnt = DB.SELECT.ESTOQUE_COMPRA_PRODUTO_TODOS.buscar()
            if etqEnt is None or len(etqEnt) == 0: raise ValueError(f"Erro ao fabricar nota de compra {id}")

            notaCompra = None
            achou = False
            for etq in etqEnt:

                if etq["id_fluxo_nota"] == id:
                   
                    if not achou:
                        achou = True
                        nota = DB.SELECT.FLUXO_NOTA_ESTOQUE_POR_ID.buscar_um(id)
                        fornecedor = SupplierClassFactory.fabricar(nota["id_representante"])
                        notaCompra = NotaCompra(id,fornecedor,etq["data"],nota["data_vencimento"])
                        
                    
                    if achou:
                        produto = ProductClassFactory.testar_e_fabricar(etq["id_produto"])
                        produto.insertPropertValue(valorUnidario=etq["valorUnidario"], quantidade= etq["quantidade"])
                        notaCompra.adicionarProduto(produto)              
                    
        except Exception as e:
            print(f"Erro ao fabricar nota de compra {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao fabricar nota de compra {e}")
            return None

        
        if notaCompra.salvar():
            cls.__purchaseNote[id]= notaCompra
            return notaCompra
        else:
            return None
